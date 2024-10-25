import React from 'react';
import Post from './Post';
import { PostContainerProps } from './types/PostContainerProps';

const PostContainer: React.FC<PostContainerProps> = ({
  posts,
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
    <div>
      <div className="main-content">
        {posts.map((post, index) => (
          <Post
            key={post.postContent.id}
            postContent={post.postContent}
            isEditable={post.isEditable || false}
            editPost={post.editPost}
            deletePost={post.deletePost}
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

export default PostContainer;
