import React from 'react';
import Post from './Post';
import { CommentContainerProps } from './types/CommentContainerProps';
import Comment from './Comment';
const CommentsContainer: React.FC<CommentContainerProps> = ({
    comments,
    nextPage,
    prevPage
    

}) => {
  const handlePreviousPage = () => {
    prevPage();
  };

  const handleNextPage = () => {
    nextPage();
  };

  return (
    <div className="comments-container">
      <div className="main-content">
        {comments.map((comment, index) => (
          <Comment
            commentContent={comment.commentContent}
            isEditable={comment.isEditable || false}
            editComment={comment.editComment}
            deleteComment={comment.deleteComment}
          />
        ))}
      </div>
      <div className="pagination-buttons">
        <button onClick={handlePreviousPage}>Previous Page</button>
        <button onClick={handleNextPage}>Next Page</button>
      </div>
    </div>
  );
};

export default CommentsContainer;
