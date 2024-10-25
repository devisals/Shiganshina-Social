import {CreateCommentProps} from './types/CreateCommentProps.tsx';
import React, { useState } from 'react';
import { useAuth } from './context/auth';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './CreateComment.css'
const CreateComment: React.FC<CreateCommentProps> = ({ onCommentCreate }) => {
  const [text, setText] = useState('');
  const auth = useAuth();
  const history = useNavigate();
  // Comment doesnt have images, so no need for image state
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // Submit form data to your backend/API here
    if (auth.user) {
      // console.log({ text });
      // Post comment and reset form
      const comment = {
        type: "comment",
        author: auth.user.author,
        comment: text,
        contentType: "text/plain",
        published: new Date().toISOString(),
        id: "",
      }
      onCommentCreate(comment).then(() => {
        setText('');
      });

    } else {
      // console.log('You must be logged in to comment');
      history('/login');
    }
  };

  return (
    <div className="create-comment-container">
      <form onSubmit={handleSubmit} className="create-comment-form">
        <textarea
          placeholder="What's happening?"
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="input-text"
        ></textarea>
        <button type="submit" className="submit-comment">Post</button>
      </form>
    </div>
  );
};

export default CreateComment;