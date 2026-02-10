-- 手动添加责任人和工作状态功能的SQL脚本

-- 1. 为 contents 表添加 work_status 字段
ALTER TABLE contents ADD COLUMN work_status TEXT DEFAULT 'planning';
CREATE INDEX ix_contents_work_status ON contents(work_status);
UPDATE contents SET work_status = 'planning' WHERE work_status IS NULL;

-- 2. 创建内容责任人关联表
CREATE TABLE content_assignees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by_user_id INTEGER,
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX ix_content_assignees_content_id ON content_assignees(content_id);
CREATE INDEX ix_content_assignees_user_id ON content_assignees(user_id);

-- 为所有现有内容添加创建者作为默认责任人
INSERT INTO content_assignees (content_id, user_id, assigned_by_user_id)
SELECT id, created_by_user_id, created_by_user_id
FROM contents
WHERE created_by_user_id IS NOT NULL;

-- 3. 创建会议责任人关联表
CREATE TABLE meeting_assignees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by_user_id INTEGER,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX ix_meeting_assignees_meeting_id ON meeting_assignees(meeting_id);
CREATE INDEX ix_meeting_assignees_user_id ON meeting_assignees(user_id);

-- 为所有现有会议添加创建者作为默认责任人
INSERT INTO meeting_assignees (meeting_id, user_id, assigned_by_user_id)
SELECT id, created_by_user_id, created_by_user_id
FROM meetings
WHERE created_by_user_id IS NOT NULL;

-- 4. 为 meetings 表添加 work_status 字段
ALTER TABLE meetings ADD COLUMN work_status TEXT DEFAULT 'planning';
CREATE INDEX ix_meetings_work_status ON meetings(work_status);

-- 根据现有的 status 字段设置 work_status
UPDATE meetings 
SET work_status = CASE 
    WHEN status = 'scheduled' THEN 'planning'
    WHEN status = 'in_progress' THEN 'in_progress'
    WHEN status = 'completed' THEN 'completed'
    WHEN status = 'cancelled' THEN 'completed'
    ELSE 'planning'
END;
