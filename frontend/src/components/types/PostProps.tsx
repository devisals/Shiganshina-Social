import { Author } from "./Author";
import { CommentContainerProps } from "./CommentContainerProps";
import { PostContentProps } from "./PostContentProps";
import { PostLayoutProps } from "./PostLayoutProps";
export type PostProps = {
    postContent: PostLayoutProps;
    isEditable?: boolean;
    editPost?: (postContent: PostLayoutProps, postID: string) => void;
    deletePost?: (postID: string) => void;

};

