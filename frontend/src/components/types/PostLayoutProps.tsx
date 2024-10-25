import { Author } from "./Author";

export type PostLayoutProps = {
    "type":string,
    // title of a post
    "title":string,
    // id of the post
    "id":string,
    // where did you get this post from?
    "source":string,
    // where is it actually from
    "origin":string,
    // a brief description of the post
    "description":string,
    // The content type of the post
    // assume either
    // text/markdown -- common mark
    // text/plain -- UTF-8
    // application/base64
    // image/png;base64 # this is an embedded png -- images are POSTS. So you might have a user make 2 posts if a post includes an image!
    // image/jpeg;base64 # this is an embedded jpeg
    // for HTML you will want to strip tags before displaying
    "contentType":string,
    "content":string,
    // the author has an ID where by authors can be disambiguated
    "author":Author,    
    // comments about the post
    // return a maximum number of comments
    // total number of comments for this post
    "count": number,
    // the first page of comments
    "comments":string,
    // commentsSrc is OPTIONAL and can be missing
    // You should return ~ 5 comments per post.
    // should be sorted newest(first) to oldest(last)
    // this is to reduce API call counts
    // "commentsSrc"?:{
    //     "type":"comments",
    //     "page":1,
    //     "size":5,
    //     "post":string
    //     "id":string,
    //     "comments":CommentLayoutProps[]
    // }
    // ISO 8601 TIMESTAMP
    "published":string,
    // visibility ["PUBLIC","FRIENDS","UNLISTED"]
    "visibility":string
    // for visibility PUBLIC means it is open to the wild web
    // FRIENDS means if we're friends I can see the post
    // FRIENDS should've already been sent the post so they don't need this
}
