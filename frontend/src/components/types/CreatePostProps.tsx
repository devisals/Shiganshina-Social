import { PostLayoutProps } from "./PostLayoutProps";

export interface CreatePostProps {
    onClose: () => void; // Adding onClose prop
    // For edit post add optional post prop
    postReturner: (postContent: PostLayoutProps) => void; // Function to return the post
    post?: PostLayoutProps; // Optional post prop
    postID?: string;
    isEdit?: boolean; // Optional isEdit prop
  }
  