import React from "react";
import { CommentProps } from "./types/CommentProps";
import "./Comment.css";
const Comment: React.FC<CommentProps> = ({ commentContent }) => {
  return (
    <div className="comment-container">
      <div className="comment-author">
        <img src={commentContent.author.profileImage} alt="Profile" />
        <h3>{commentContent.author.displayName}</h3>
      </div>
      <div className="comment-content">
        <p>{commentContent.comment}</p>
      </div>
    </div>
  );
};

export default Comment;
