CREATE DATABASE IF NOT EXISTS zhihu;
USE zhihu;

-- 用户表
CREATE TABLE User (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Username VARCHAR(50) NOT NULL UNIQUE,
    Email VARCHAR(255) NOT NULL UNIQUE,
    Password VARCHAR(255) NOT NULL,
    RegistrationTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Profile TEXT,
    Avatar VARCHAR(255),
    Gender TINYINT NOT NULL CHECK (Gender IN (0, 1)),
    CONSTRAINT chk_gender CHECK (Gender IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 话题表（需先创建，供Question表引用）
CREATE TABLE Topic (
    TopicID INT PRIMARY KEY AUTO_INCREMENT,
    TopicName VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 问题表
CREATE TABLE Question (
    QuestionID INT PRIMARY KEY AUTO_INCREMENT,
    Title VARCHAR(255) NOT NULL,
    Content TEXT NOT NULL,
    UserID INT NOT NULL,
    TopicID INT NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (TopicID) REFERENCES Topic(TopicID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 回答表
CREATE TABLE Answer (
    AnswerID INT PRIMARY KEY AUTO_INCREMENT,
    Content TEXT NOT NULL,
    UserID INT NOT NULL,
    QuestionID INT NOT NULL,
    AnswerTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UpvoteCount INT NOT NULL DEFAULT 0 CHECK (UpvoteCount >= 0),
    AnswerIP VARCHAR(45) NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (QuestionID) REFERENCES Question(QuestionID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 评论表
CREATE TABLE Comment (
    CommentID INT PRIMARY KEY AUTO_INCREMENT,
    Content TEXT NOT NULL,
    UserID INT NOT NULL,
    AnswerID INT NOT NULL,
    CommentTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CommentIP VARCHAR(45) NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (AnswerID) REFERENCES Answer(AnswerID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 评价表
CREATE TABLE Evaluation (
    EvaluationID INT PRIMARY KEY AUTO_INCREMENT,
    Content TEXT NOT NULL,
    UserID INT NOT NULL,
    EvaluationTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    EvaluationIP VARCHAR(45) NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 私信表
CREATE TABLE PrivateMessage (
    MessageID INT PRIMARY KEY AUTO_INCREMENT,
    SenderID INT NOT NULL,
    ReceiverID INT NOT NULL,
    Content TEXT NOT NULL,
    SendTime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SenderID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (ReceiverID) REFERENCES User(UserID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 索引优化

-- 唯一索引
CREATE UNIQUE INDEX idx_unique_email ON User(Email);

-- 非聚集索引
CREATE INDEX idx_user_registration_time ON User(RegistrationTime);
CREATE INDEX idx_question_createtime ON Question(CreateTime);
CREATE INDEX idx_answer_upvote ON Answer(UpvoteCount);
CREATE INDEX idx_question_user ON Question(UserID);
CREATE INDEX idx_answer_question ON Answer(QuestionID);
CREATE INDEX idx_comment_answer ON Comment(AnswerID);



-- 行列子集视图，带表达式视图，分组视图

-- 显示用户基础信息（隐藏敏感字段）
CREATE VIEW UserBasicInfo AS
SELECT Username, Email, RegistrationTime
FROM User;

-- 统计回答内容的长度和格式化时间
CREATE VIEW AnswerContentStats AS
SELECT 
    AnswerID,
    LENGTH(Content) AS ContentLength,  -- 计算内容长度
    DATE_FORMAT(AnswerTime, '%Y-%m-%d') AS AnswerDate  -- 格式化时间
FROM Answer;

-- 统计每个用户的回答数量和平均点赞数
CREATE VIEW UserAnswerSummary AS
SELECT 
    UserID,
    COUNT(AnswerID) AS TotalAnswers,
    AVG(UpvoteCount) AS AvgUpvotes
FROM Answer
GROUP BY UserID;