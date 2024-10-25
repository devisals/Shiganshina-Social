// PostViewer.tsx
import React from 'react';
import './PostViewer.css'; // Make sure to create this CSS for styling
import { Close } from '@mui/icons-material';
import { PostLayoutProps } from './types/PostLayoutProps';
import Post from './Post'; // Assuming this is your Post component

interface PostViewerProps {
  onClose: () => void;
  postContent?: PostLayoutProps;
  post?: React.ReactNode;
}

const PostViewer: React.FC<PostViewerProps> = ({ onClose, postContent, post }) => {
  return (
    <div className="post-viewer-overlay">
      <div className="post-viewer-container">
        <button onClick={onClose} className="post-viewer-close-button">
          <Close />
        </button>
        {postContent ? (
          <Post postContent={postContent} />
        ) : post ? (
          post
        ) : (
          <div>No post content available.</div>
        )}
      </div>
    </div>
  );
};

export default PostViewer;
