-- ============================================================================
-- 会议纪要智能转写系统 — MySQL 表结构（四张表）
--
-- 说明：按源码数据模型（app/store/memory.py、app/worker.py、app/api/meetings.py、
--       app/config.py）拆分。每场会议都有全局唯一 meeting_id（uuid4().hex），
--       四张表通过该业务键关联：
--           1) meeting_records        —— 会议记录（主表：上传元数据 + 处理状态）
--           2) meeting_transcripts    —— 会议转录（转写全文，一场会议 1 行）
--           3) meeting_word_frequency —— 词频明细（一场会议多行）
--           4) meeting_summaries      —— 会议总结（一场会议 1 行）
--
-- 关键约束：
--   * meeting_id 在四表中均为业务主键/关联键。
--   * meeting_records.meeting_id 唯一（每场会议一行主记录）。
--   * meeting_transcripts / meeting_summaries 对每场会议唯一（1:1）。
--   * meeting_word_frequency 用 (meeting_id, word) 联合唯一索引（幂等/upsert）。
--   * 三张子表均以 meeting_id 外键引用主表，删除会议时级联删除其转录/词频/总结。
--
-- 字段与源码对照：
--   create_meeting 存：meeting_id, title, file_name, file_path, file_size,
--                      status, progress, stage, duration_sec, chunk_count,
--                      transcript, summary, summary_is_mock, error_message, 时间戳
--   worker 更新：status/progress/stage/chunk_count/transcript/summary/summary_is_mock/error_message
--   词频明细 save_words：{word, freq}（M5 Counter+jieba 输出）
--   总结接口额外返回 model（template | deepseek-chat）
--
-- 使用：mysql -u<user> -p < init.sql
-- 目标：MySQL 8.0，库名 meeting_minutes（与 app/config.py 的 MYSQL_DB 一致）。
-- ============================================================================

-- 创建数据库（若不存在）
CREATE DATABASE IF NOT EXISTS `meeting_minutes`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `meeting_minutes`;

-- ----------------------------------------------------------------------------
-- 表 1：meeting_records —— 会议记录（主表）
--   每场会议一行，记录上传元数据与处理状态；其余三张表以 meeting_id 关联。
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `meeting_records` (
    `id`             BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT COMMENT '自增物理主键',
    `meeting_id`     VARCHAR(64)      NOT NULL                COMMENT '全局唯一会议ID（uuid4 hex，业务主键/幂等键）',
    `title`          VARCHAR(255)     NOT NULL DEFAULT ''     COMMENT '会议标题（默认取文件名）',
    `file_name`      VARCHAR(255)     NOT NULL DEFAULT ''     COMMENT '原始上传文件名',
    `file_path`      VARCHAR(512)     NOT NULL DEFAULT ''     COMMENT '原始音频落盘路径',
    `file_size`      BIGINT UNSIGNED  NOT NULL DEFAULT 0      COMMENT '文件大小（字节）',
    `duration_sec`   INT UNSIGNED     NULL                    COMMENT '音频时长（秒），未解析为 NULL',
    `chunk_count`    INT UNSIGNED     NOT NULL DEFAULT 0      COMMENT '分块数（进度分母）',
    `status`         VARCHAR(20)      NOT NULL DEFAULT 'queued' COMMENT '状态：queued|processing|completed|failed',
    `progress`       TINYINT UNSIGNED NOT NULL DEFAULT 0      COMMENT '进度 0-100',
    `stage`          VARCHAR(20)      NOT NULL DEFAULT 'queued' COMMENT '阶段：queued|chunking|asr|freq|summary|done',
    `error_message`  VARCHAR(512)     NULL                    COMMENT '失败原因（成功为 NULL）',
    `created_at`     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_meeting_id` (`meeting_id`),
    KEY `idx_status_created` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会议记录主表';

-- ----------------------------------------------------------------------------
-- 表 2：meeting_transcripts —— 会议转录
--   一场会议 1 行（meeting_id 唯一），存转写全文与所用引擎。
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `meeting_transcripts` (
    `id`             BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT COMMENT '自增物理主键',
    `meeting_id`     VARCHAR(64)      NOT NULL                COMMENT '关联会议ID（一场会议仅一行，幂等键）',
    `transcript`     LONGTEXT         NULL                    COMMENT '转写全文（完成前为 NULL）',
    `asr_provider`   VARCHAR(30)      NOT NULL DEFAULT 'mock' COMMENT '转写引擎：mock|baidu|whisper|xfyun|ali',
    `created_at`     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_meeting_id` (`meeting_id`),
    CONSTRAINT `fk_transcript_meeting` FOREIGN KEY (`meeting_id`)
        REFERENCES `meeting_records` (`meeting_id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会议转录表';

-- ----------------------------------------------------------------------------
-- 表 3：meeting_word_frequency —— 词频明细
--   一场会议多行；(meeting_id, word) 联合唯一索引，幂等/upsert 用。
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `meeting_word_frequency` (
    `id`             BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT COMMENT '自增物理主键',
    `meeting_id`     VARCHAR(64)      NOT NULL                COMMENT '关联会议ID',
    `word`           VARCHAR(64)      NOT NULL                COMMENT '词',
    `freq`           INT UNSIGNED     NOT NULL DEFAULT 0      COMMENT '频次',
    `created_at`     DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_meeting_word` (`meeting_id`, `word`),
    KEY `idx_meeting_id` (`meeting_id`),
    CONSTRAINT `fk_word_freq_meeting` FOREIGN KEY (`meeting_id`)
        REFERENCES `meeting_records` (`meeting_id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会议词频明细表';

-- ----------------------------------------------------------------------------
-- 表 4：meeting_summaries —— 会议总结
--   一场会议 1 行（meeting_id 唯一），存结构化纪要、是否模板降级及生成模型。
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `meeting_summaries` (
    `id`               BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT COMMENT '自增物理主键',
    `meeting_id`       VARCHAR(64)      NOT NULL                COMMENT '关联会议ID（一场会议仅一行，幂等键）',
    `summary`          TEXT             NULL                    COMMENT '结构化纪要文本（主题/要点/结论/待办）',
    `summary_is_mock`  TINYINT(1)       NOT NULL DEFAULT 0      COMMENT '是否模板降级（1=mock 模板，0=DeepSeek 真实）',
    `model`            VARCHAR(50)      NOT NULL DEFAULT 'template' COMMENT '生成模型：template | deepseek-chat',
    `created_at`       DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`       DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_meeting_id` (`meeting_id`),
    CONSTRAINT `fk_summary_meeting` FOREIGN KEY (`meeting_id`)
        REFERENCES `meeting_records` (`meeting_id`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会议总结表';

-- ============================================================================
-- 附：按需示例（演示幂等写入流程，便于理解后端存什么）
-- 流程：先写 meeting_records（queued→processing→completed），再写转录/词频/总结。
-- ============================================================================
--
-- -- 1) 上传后建主记录（status=queued）
-- INSERT INTO meeting_records
--     (meeting_id, title, file_name, file_path, file_size)
-- VALUES
--     ('7f9c0ab3e5d14c2e8b6f4a1d9e0c77aa', '产品周会', 'rec.m4a',
--      '/data/uploads/7f9c0ab3e5d14c2e8b6f4a1d9e0c77aa/raw.m4a', 8388608);
--
-- -- 2) 处理完成后更新主记录状态 + 写转录全文
-- UPDATE meeting_records
--    SET status='completed', progress=100, stage='done'
--  WHERE meeting_id='7f9c0ab3e5d14c2e8b6f4a1d9e0c77aa';
--
-- INSERT INTO meeting_transcripts (meeting_id, transcript, asr_provider)
-- VALUES ('7f9c0ab3e5d14c2e8b6f4a1d9e0c77aa', '这是一段转写全文……', 'mock')
-- ON DUPLICATE KEY UPDATE transcript=VALUES(transcript), asr_provider=VALUES(asr_provider);
--
-- -- 3) 词频明细（幂等 upsert：一场会议每词一行）
-- INSERT INTO meeting_word_frequency (meeting_id, word, freq) VALUES
--     ('7f9c0ab3e5d14c2e8b6f4a1d9e0c77aa', '会议', 12),
--     ('7f9c0ab3e5d14c2e8b6f4a1d9e0c77aa', '进度', 8)
-- ON DUPLICATE KEY UPDATE freq=VALUES(freq);
--
-- -- 4) 会议总结（幂等 upsert：一场会议一行）
-- INSERT INTO meeting_summaries (meeting_id, summary, summary_is_mock, model)
-- VALUES ('7f9c0ab3e5d14c2e8b6f4a1d9e0c77aa',
--         '【主题】…\n【要点】…\n【结论】…\n【待办】…', 1, 'template')
-- ON DUPLICATE KEY UPDATE
--     summary=VALUES(summary), summary_is_mock=VALUES(summary_is_mock), model=VALUES(model);
--
-- ============================================================================
