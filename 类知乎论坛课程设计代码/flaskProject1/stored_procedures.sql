-- 更新问题回答数的存储过程
DELIMITER //
CREATE PROCEDURE UpdateQuestionAnswerCount(IN question_id INT)
BEGIN
    UPDATE Question 
    SET AnswerCount = (
        SELECT COUNT(*) 
        FROM Answer 
        WHERE QuestionID = question_id
    )
    WHERE QuestionID = question_id;
END //
DELIMITER ;

-- 更新用户统计信息的存储过程
DELIMITER //
CREATE PROCEDURE UpdateUserStats(IN user_id INT)
BEGIN
    UPDATE User 
    SET 
        QuestionCount = (
            SELECT COUNT(*) 
            FROM Question 
            WHERE UserID = user_id
        ),
        AnswerCount = (
            SELECT COUNT(*) 
            FROM Answer 
            WHERE UserID = user_id
        ),
        CommentCount = (
            SELECT COUNT(*) 
            FROM Comment 
            WHERE UserID = user_id
        ),
        TotalUpvotes = (
            SELECT COALESCE(SUM(UpvoteCount), 0)
            FROM Answer 
            WHERE UserID = user_id
        )
    WHERE UserID = user_id;
END //
DELIMITER ;

-- 获取热门问题的存储过程
DELIMITER //
CREATE PROCEDURE GetHotQuestions(IN limit_count INT)
BEGIN
    SELECT 
        q.QuestionID,
        q.Title,
        q.Content,
        q.CreateTime,
        u.Username,
        t.TopicName,
        COUNT(a.AnswerID) as AnswerCount,
        COALESCE(SUM(a.UpvoteCount), 0) as TotalUpvotes
    FROM Question q
    JOIN User u ON q.UserID = u.UserID
    JOIN Topic t ON q.TopicID = t.TopicID
    LEFT JOIN Answer a ON q.QuestionID = a.QuestionID
    GROUP BY q.QuestionID
    ORDER BY TotalUpvotes DESC, AnswerCount DESC
    LIMIT limit_count;
END //
DELIMITER ;

-- 1. 获取话题及其问题数量的存储过程
DELIMITER //
CREATE PROCEDURE GetTopicWithQuestionCount(IN p_topic_id INT)
BEGIN
    SELECT t.*, COUNT(q.QuestionID) as question_count
    FROM Topic t
    LEFT JOIN Question q ON t.TopicID = q.TopicID
    WHERE t.TopicID = p_topic_id
    GROUP BY t.TopicID;
END //
DELIMITER ;

-- 2. 获取用户发布的所有问题的存储过程
DELIMITER //
CREATE PROCEDURE GetUserQuestions(IN p_user_id INT)
BEGIN
    SELECT q.*, t.TopicName, COUNT(a.AnswerID) as answer_count
    FROM Question q
    JOIN Topic t ON q.TopicID = t.TopicID
    LEFT JOIN Answer a ON q.QuestionID = a.QuestionID
    WHERE q.UserID = p_user_id
    GROUP BY q.QuestionID;
END //
DELIMITER ;

-- 3. 获取问题及其回答数量的存储过程
DELIMITER //
CREATE PROCEDURE GetQuestionWithAnswerCount(IN p_question_id INT)
BEGIN
    SELECT q.*, t.TopicName, u.Username, COUNT(a.AnswerID) as answer_count
    FROM Question q
    JOIN Topic t ON q.TopicID = t.TopicID
    JOIN User u ON q.UserID = u.UserID
    LEFT JOIN Answer a ON q.QuestionID = a.QuestionID
    WHERE q.QuestionID = p_question_id
    GROUP BY q.QuestionID;
END //
DELIMITER ; 