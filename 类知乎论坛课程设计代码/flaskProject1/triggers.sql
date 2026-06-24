-- 添加回答后更新问题回答数的触发器
DELIMITER //
CREATE TRIGGER after_answer_insert
AFTER INSERT ON Answer
FOR EACH ROW
BEGIN
    CALL UpdateQuestionAnswerCount(NEW.QuestionID);
    CALL UpdateUserStats(NEW.UserID);
END //
DELIMITER ;

-- 删除回答后更新问题回答数的触发器
DELIMITER //
CREATE TRIGGER after_answer_delete
AFTER DELETE ON Answer
FOR EACH ROW
BEGIN
    CALL UpdateQuestionAnswerCount(OLD.QuestionID);
    CALL UpdateUserStats(OLD.UserID);
END //
DELIMITER ;

-- 添加评论后更新用户统计信息的触发器
DELIMITER //
CREATE TRIGGER after_comment_insert
AFTER INSERT ON Comment
FOR EACH ROW
BEGIN
    CALL UpdateUserStats(NEW.UserID);
END //
DELIMITER ;

-- 删除评论后更新用户统计信息的触发器
DELIMITER //
CREATE TRIGGER after_comment_delete
AFTER DELETE ON Comment
FOR EACH ROW
BEGIN
    CALL UpdateUserStats(OLD.UserID);
END //
DELIMITER ;

-- 更新回答点赞数后更新用户统计信息的触发器
DELIMITER //
CREATE TRIGGER after_answer_update
AFTER UPDATE ON Answer
FOR EACH ROW
BEGIN
    IF NEW.UpvoteCount != OLD.UpvoteCount THEN
        CALL UpdateUserStats(NEW.UserID);
    END IF;
END //
DELIMITER ; 