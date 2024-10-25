import React, { useState, useEffect } from 'react';
import './Post.css';
import { PostProps } from './types/PostProps.tsx'; // Assuming you create a types.ts for custom types
import ThumbUp from '@mui/icons-material/ThumbUp';
import Share from '@mui/icons-material/Share';
import Reply from '@mui/icons-material/Reply';
import Comment from '@mui/icons-material/Comment';
import { Delete, Edit, Pages } from '@mui/icons-material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { CommentProps } from './types/CommentProps.tsx'; // Assuming you create a types.ts for custom types
import CreatePost from './CreatePost.tsx';
import { PostLayoutProps } from './types/PostLayoutProps.tsx';
import { useAuth } from './context/auth.tsx';
import axios from 'axios';
import { getIdFromUrlRegex, backendHost } from './types/Host.tsx';
import { CommentLayoutProps } from './types/CommentLayoutProps.tsx';
import CommentsContainer from './CommentsContainer.tsx';
import CreateComment from './CreateComment.tsx';
import Markdown from 'react-markdown'
import Cookies from 'js-cookie';
import { getAuthorFollowers } from './types/FollowersHelper.tsx';
import { json } from 'react-router-dom';


const Post: React.FC<PostProps> = ({
  postContent,
  isEditable = false,
  editPost = (postContent: PostLayoutProps, postID: string) => { },
  deletePost = (postID: string) => { },
}) => {
  const [likes, setLikes] = useState<number>(0);
  const [likesArray, setLikesArray] = useState<string[]>([]); // Add state for likes
  const [comments, setComments] = useState<CommentProps[]>([]); // Add state for comments
  const [showComments, setShowComments] = useState<boolean>(false); // State to toggle comment visibility
  const [editMode, setEditMode] = useState<boolean>(false); // State to toggle edit mode
  const [postContentState, setPostContentState] = useState<PostLayoutProps>(postContent);
  const [pageNumber, setPageNumber] = useState(1);
  const [loadingComments, setLoadingComments] = useState<boolean>(false);
  const [isLiked, setIsLiked] = useState<boolean>(false);
  const [isSharedPost, setIsSharedPost] = useState<boolean>(false);
  // Add a state for showing the share notification
  const [showSharePopup, setShowSharePopup] = useState(false);
  const [showImageSharePopup, setshowImageSharePopup] = useState(false);
  const auth = useAuth();


  // eslint-disable-next-line @typescript-eslint/no-unused-vars

  const user = postContent.author.displayName;
  const profilePicture = postContent.author.profileImage;
  const ghuburl = postContent.author.github;
  const published = postContent.published;
  const postID = postContent.id;
  const origin = postContent.origin;
  const size = 5;
  // Connect to backend later...
  const postContentSetter = async (postContentNew: PostLayoutProps): Promise<void> => {
    setPostContentState(postContentNew); // Update the state

    await editPost(postContentNew, postID); // Call the editPost function with the new content
  };

  // useEffect(() => {
  // }, [postContentState]); // Dependency array includes `postContentState`
  const fetchLikes = async () => {
    const refinedAuthorID = getIdFromUrlRegex(postContentState.author.id);
    const refinedPostID = getIdFromUrlRegex(postID);
    const response = await axios.get(`/api/authors/${refinedAuthorID}/posts/${refinedPostID}/likes?all`);
    setLikes(response.data.items.length);
    setLikesArray(response.data.items);
    // console.log(response.data);
  };

  useEffect(() => {
    // console.log('origin', origin)
    if (!auth.user.author) {
      // check the cookies
      const cookiesAuth = Cookies.get('auth');
      if (cookiesAuth) {
        const authUser = JSON.parse(cookiesAuth);
        // console.log('cookies', authUser);
        auth.setUser(authUser);
      }

    }

    // load the likes on the post


    fetchLikes();

    // check if the post is shared (if the source doesn't match origin url)
    if (origin !== window.location.href) {
      setIsSharedPost(true);
    }

  }, []);

  useEffect(() => {
    // refresh likes every 5 seconds
    const interval = setInterval(() => {
      fetchLikes();
    }, 10000);
    return () => clearInterval(interval);
  }, [likes, likesArray])


  const handleLike = async (): Promise<void> => {
    if (!auth.user.author) return;
    if (!isLiked) {
      // post the like and increment the like count
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth.user.token}`
      };

      const refinedAuthorID = getIdFromUrlRegex(postContentState.author.id);
      const refinedPostID = getIdFromUrlRegex(postID);
      // console.log(refinedAuthorID);
      try {
        // console.log("np560404gjrkwrkfger", backendHost);
        // flag i guess.
        const likeObject = {
          type: "Like",
          summary: `${auth.user.author.displayName} Liked the post`,
          author: auth.user.author,
          object: postID
        }

        const inboxObject = {
          type: "inbox",
          author: auth.user.author.id,
          items: [likeObject]
        }

        const response = await axios.post(`/api/authors/${refinedAuthorID}/inbox?all`, inboxObject, { headers });
        setLikes(likes + 1);
        setIsLiked(true);
      } catch (error: any) {
        // if the status is 400 the post has already been liked

        if (error.response.status === 400) {
          alert("You have already liked this post");
        } else {
          alert("Error liking the post");
        }
      }


    }

  };

  const refineCommentsURL = (url: string): string => {
    // const apiStartIndex = url.indexOf('/api'); // Find the start of the API URL
    // const apiUrl = apiStartIndex !== -1 ? url.substring(apiStartIndex) : url;
    // const commentUrl = apiUrl.endsWith('/') ? apiUrl.slice(0, -1) : apiUrl; // Remove trailing slash if present
    // return commentUrl;

    const authorsStartIndex = url.indexOf('/authors');
    if (authorsStartIndex === -1) {
      return url;
    } else {
      const authorsUrl = url.substring(authorsStartIndex);
      // append /api to the url beginning
      const finalURL = `/api${authorsUrl}`;
      return finalURL;
    }
  }

  const onCommentCreate = async (comment: CommentLayoutProps): Promise<void> => {
    // post the new comment 
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${auth.user.token}`
    };
    const url = postContent.comments;
    const commentUrl = refineCommentsURL(url);
    const refinedComment = {
      comment: comment.comment,
    }
    try {
      const response = await axios.post(commentUrl + '?all', refinedComment, { headers });
      const createdComment = response.data;
      retrieveRepliesOnPage(pageNumber);
    } catch (error) {
      alert("Error posting comment");
      // console.log(error);
    }


  }


  async function nextPage() {
    // Increment page number first

    await retrieveRepliesOnPage(pageNumber + 1);



    // if there is an error set the page number back to the previous value

  }

  async function previousPage() {
    // Increment page number first
    if (pageNumber === 1) {
      return;
    }
    await retrieveRepliesOnPage(pageNumber - 1);
  }

  const handleCopyLink = (): void => {
    // Construct the link to be shared
    // get the current domain
    const currentDomain = window.location.origin;
    // remove all paths and query strings in the url
    let currentDomainRegex;
    if (currentDomain.includes("https")) {
      currentDomainRegex = /https?:\/\/[^\/]+/;
    } else {
      currentDomainRegex = /http?:\/\/[^\/]+/;
    }

    const domain = currentDomain.match(currentDomainRegex);
    const postLink = `${domain}/profile?id=${getIdFromUrlRegex(postContent.author.id)}&post=${getIdFromUrlRegex(postID)}`;


    // Use the Clipboard API to copy the link
    navigator.clipboard.writeText(postLink).then(() => {
      // Show the popup/notification
      setShowSharePopup(true);

      // Hide the popup after a few seconds
      setTimeout(() => {
        setShowSharePopup(false);
      }, 3000); // Adjust time as needed
    }).catch(err => {
      console.error('Failed to copy the link: ', err);
    });
  };


  const handleImageLink = (): void => {
    const currentDomain = window.location.origin;
    let currentDomainRegex;
    if (currentDomain.includes("https")) {
      currentDomainRegex = /https?:\/\/[^\/]+/;
    } else {
      currentDomainRegex = /http?:\/\/[^\/]+/;
    }

    const domain = currentDomain.match(currentDomainRegex);

    const ImageLink = `${domain}/api/authors/${getIdFromUrlRegex(postContent.author.id)}/posts/${getIdFromUrlRegex(postID)}/image?all`;


    // Use the Clipboard API to copy the link
    navigator.clipboard.writeText(ImageLink).then(() => {
      // Show the popup/notification
      setshowImageSharePopup(true);

      setTimeout(() => {
        setshowImageSharePopup(false);
      }, 3000); // Adjust time as needed
    }).catch(err => {
      console.error('Failed to copy the link: ', err);
    });
  };

  async function handleDeletePost() {

    // make a call to the backend to delete the post
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${auth.user.token}`
    };

    // check if the authorID is already refined (i.e does not have "https://")
    const refinedAuthorID = getIdFromUrlRegex(auth.user.author.id);
    const refinedPostID = getIdFromUrlRegex(postID);
    // console.log(refinedAuthorID);
    try {
      const response = await axios.delete(`/api/authors/${refinedAuthorID}/posts/${refinedPostID}?all`, { headers })
      await deletePost(postID);
      // console.log(response);

    } catch {
      alert("Error deleting the post");
    }


  };
  // Simulate retrieving comments
  const retrieveReplies = async (): Promise<void> => {
    if (!showComments) {
      setShowComments(true);
      setLoadingComments(true); // Start loading
      await retrieveRepliesOnPage(1);
      setLoadingComments(false); // Finish loading
    } else {
      setShowComments(false);
    }
  };
  const retrieveRepliesOnPage = async (commentPage: number): Promise<void> => {
    setLoadingComments(true); // Start loading
    // fetch the comments
    // console.log(showComments);


    const url = postContent.comments;
    const commentUrl = refineCommentsURL(url);
    const commentUrlPage = `${commentUrl}?page=${commentPage}&size=${size}&all`;
    try {
      const response = await axios.get(commentUrlPage);
      setPageNumber(commentPage);
      const rawComments = response.data.items;
      const refinedComments: CommentProps[] = [];
      for (let i = 0; i < rawComments.length; i++) {
        const comment = rawComments[i];
        const refinedComment: CommentProps = {
          commentContent: comment
        }
        refinedComments.push(refinedComment);

      }
      setComments(refinedComments);
    } catch {

    } finally {
      setLoadingComments(false); // Finish loading
    }

  };

  // Call retrieveReplies on component mount
  // NOTE THIS IS VERY INEFFICIENT, but it's a simple example
  // In reality once backend is ready, we will just use this to get the number of comments
  // then once the button is clicked we will call retrieveReplies


  const handleCloseEdit = (): void => {
    setEditMode(false); // Simply exit edit mode without saving changes
  };

  const handlePostEdit = (): void => {
    setEditMode(true);
  };

  const definePostContent = (): React.ReactNode => {
    if (postContentState.contentType.includes("text")) {
      if (postContentState.contentType.includes("markdown")) {
        return (
          <div className="post-text"><Markdown className={"markdown-content"}>{postContentState.content}</Markdown></div>
        );
      }
      return (
        <div className="post-text">{postContentState.content}</div>
      );
    } else if (postContentState.contentType.includes("image")) {
      // Assuming the base64 string is ready to be used directly or
      // prepend 'data:image/png;base64,' if the base64 string does not start with 'data:image'
      const imageSrc = postContentState.content.startsWith('data:image') ? postContentState.content : `data:image/png;base64,${postContentState.content}`;
      return (
        <div className="post-images">
          <img src={imageSrc} alt='Posted Image'></img>
        </div>
      );
    }
  };


  const parseDate = () => {
    const dateObject = new Date(published);

    // Customize these options as needed
    // Customize these options as needed
    const dateOptions: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'long', day: 'numeric' };
    const timeOptions: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit', hour12: true };


    const dateString = dateObject.toLocaleDateString('en-US', dateOptions);
    const timeString = dateObject.toLocaleTimeString('en-US', timeOptions);

    return `${dateString}, ${timeString}`;
  }

  const handleShare = async (): Promise<void> => {
    // check if the user is logged in
    if (!auth.user.author) {
      return;
    }

    // to share the post, send it to all people following you's inbox 
    // get the author's followers
    const refinedAuthorID = getIdFromUrlRegex(auth.user.author.id) || '';
    const followers = await getAuthorFollowers(refinedAuthorID);

    // create the share object

    const inboxObject = {
      type: "inbox",
      author: postContent.author.id,
      items: [postContent]
    }
    // console.log(JSON.stringify(inboxObject));
    // send it to the inox of all followers
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${auth.user.token}`
    };

    for (const follower of followers) {
      try {
        const encodedURL = encodeURIComponent(follower.id)
        // console.log('encodedshit', encodedURL)
        const response = await axios.post(`/api/authors/${getIdFromUrlRegex(follower.id)}/inbox?all`, inboxObject, { headers });

      } catch (error: any) {
        // console.log(error);
      }
    }

  };

  if (editMode) {
    return (
      <div className="edit-container">
        <CreatePost
          postReturner={postContentSetter}
          onClose={handleCloseEdit}
          post={postContent}
          postID={postID}
          isEdit={true}
        />
      </div>
    );
  }

  function isImagePost() {
    return postContent.contentType.includes("image");
  }

  return (
    <>
      <div className="post-container">
        <div className="title-container">
          <div className="post-title">{postContentState.title}</div>
        </div>
        <div className="description-container">
          <div className="post-description">
            Description: {postContentState.description}
          </div>
        </div>
        <div className="user-info">
          <div className="pfp-container">
            <img src={profilePicture} alt={`${user}'s profile`} className="profile-picture" />
          </div>
          <div className="uname-container">
            <div className="user-name">{user}</div>
          </div>
          <div className="email-container">
            <div className="user-email">{ghuburl}</div>
          </div>
        </div>
        <div className="date-container">
          <div className="post-date">Published: {parseDate()}</div>
        </div>
        <div className="post-content">

          {definePostContent()}
        </div>

        <div className="post-buttons">
          <div className="post-interactions">
            <button onClick={handleLike}>
              <ThumbUp />
              <div className="int-btn-txt">{likes}</div></button>
            <button onClick={handleCopyLink}>
              <ContentCopyIcon />
              <div className="int-btn-txt">Copy Link{ }</div></button>
            {isImagePost() && (<button onClick={handleImageLink}>
              <Pages />
              <div className="int-btn-txt">Copy Image{ }</div></button>)}
            <button onClick={handleShare}>
              <Share />
              <div className="int-btn-txt">Share{ }</div></button>
            <button onClick={retrieveReplies}>
              <Comment />
              <div className="int-btn-txt">Comments{ }</div> {/* Updated to show the number of comments */}
            </button>
          </div>


          {isEditable && (
            <div className="edit-post">
              <button onClick={handlePostEdit}>
                <Edit />
                <div className="edit-post-button">Edit</div></button>

              <button onClick={handleDeletePost}>
                <Delete />
                <div className="delete-post-button">Delete</div></button>

            </div>
          )}
        </div>
      </div>
      {showSharePopup && (
        <div className="share-popup">Post Link copied to clipboard!</div>
      )}
      {showImageSharePopup && (
        <div className="share-popup">Image Link copied to clipboard!</div>
      )}

      {showComments && auth.user.author && (

        <CreateComment onCommentCreate={onCommentCreate} />
      )}

      {loadingComments == false && showComments == true && (

        <CommentsContainer comments={comments} nextPage={nextPage} prevPage={previousPage} />
      )}

    </>
  );
};

export default Post;
