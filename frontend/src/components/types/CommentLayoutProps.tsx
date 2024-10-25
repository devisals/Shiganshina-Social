import { Author } from "./Author"

export type CommentLayoutProps = {
    "type":string,
    "author":Author,
    "comment":string,
    "contentType":string,
    // ISO 8601 TIMESTAMP
    "published":string,
    // ID of the Comment (UUID)
    "id":string
}