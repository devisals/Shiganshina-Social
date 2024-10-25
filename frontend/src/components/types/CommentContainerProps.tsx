import { CommentProps } from './CommentProps';
export type CommentContainerProps = {
    comments: CommentProps[];
    nextPage: () => void;
    prevPage: () => void;
};