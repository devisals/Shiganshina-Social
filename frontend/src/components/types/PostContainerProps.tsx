import { PostProps } from './PostProps';
export type PostContainerProps = {
    posts: PostProps[];
    nextPage: () => void;
    prevPage: () => void;
};