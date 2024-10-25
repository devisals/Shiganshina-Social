import { Author } from "./Author";
import { CommentLayoutProps } from "./CommentLayoutProps";

export type CommentProps = {
    commentContent: CommentLayoutProps;
    isEditable?: boolean;
    editComment?: () => void;
    deleteComment?: () => void;
  };
