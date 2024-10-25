import {CommentLayoutProps} from "./CommentLayoutProps";
export interface CreateCommentProps {
    onCommentCreate: (comment: CommentLayoutProps) => Promise<void>;

  }
  