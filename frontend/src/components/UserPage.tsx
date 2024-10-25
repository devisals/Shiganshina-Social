import React, { useState, useEffect } from 'react';
import Sidebar from "./Sidebar.tsx";
import { Author } from './types/Author.tsx';
import '../App.css';
import './Home.css';
import axios from 'axios';
import PostContainer from './PostsContainer.tsx';
// Import the props type directly from the CommentContainer component if it's exported, or redefine it here
import { PostProps } from './types/PostProps.tsx'; // Assuming you create a types.ts for custom types
import CreatePost from './CreatePost.tsx';
import { useAuth } from './context/auth.tsx';
import { useNavigate } from 'react-router-dom';
import { PostLayoutProps } from './types/PostLayoutProps.tsx';
import { backendHost, backendHost2, getIdFromUrlRegex } from './types/Host.tsx';
import { getAuthorFollowers, followAuthor, unFollowAuthor, isUserFollowingAuthor } from './types/FollowersHelper.tsx';
import Cookies from 'js-cookie';
import PostViewer from './PostViewer.tsx';
const UserPage: React.FC = () => {
  const history = useNavigate();
  const [isCreatePostOpen, setIsCreatePostOpen] = useState(false);
  const [posts, setPosts] = useState<PostProps[]>([]);
  const [urlId, setUrlId] = useState("");
  const [author, setAuthor] = useState<Author | null>(null);
  const auth = useAuth();
  const [pageNumber, setPageNumber] = useState(1);
  const [fetchNewItems, setFetchNewItems] = useState(false);
  const [followerCount, setFollowerCount] = useState(0);
  const [isUserFollowing, setIsUserFollowing] = useState(false);
  const [postShown, setPostShown] = useState(false);
  const [currentPost, setCurrentPost] = useState<PostLayoutProps | null>(null);
  const [isFollowPending, setIsFollowPending] = useState(false);
  const size = 15;
  const [isUserLoggedIn, setIsUserLoggedIn] = useState(false);
  const hostApiUrl = backendHost
  // console.log(hostApiUrl); // Output: http://example.com/api/

  function onPostClose() {
    setPostShown(false);
    setCurrentPost(null); // Clear the current post when closing
  }

  const getPostsOnPage = async (pageNumber: number, authorId?: string): Promise<void> => {
    setPageNumber(pageNumber);
    // console.log('pageNumber', pageNumber);
    if (!authorId) return; // Ensure we have an author ID
    // console.log('fetching posts');
    try {
      // console.log('fetching posts');
      let response;

      if (auth.user && auth.user.author) {
        const headers = {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${auth.user.token}`
        };

        // console.log("user is viewing the profile authenticated")
        response = await axios.get(`/api/authors/${authorId}/posts?page=${pageNumber}&size=${size}&all`, { headers });
      } else {
        // console.log("author is viewing somoene else's profile")
        response = await axios.get(`/api/authors/${authorId}/posts?page=${pageNumber}&size=${size}&all`);
      }

      const ghubResp = await axios.put('api/update_github');
      // console.log('ghub resp', ghubResp);
      const responseItems = response.data.items;
      const fetchedPosts = [];
      for (let i = 0; i < responseItems.length; i++) {
        const respPost = responseItems[i];
        const post: PostProps = {
          postContent: respPost,
          isEditable: false,
          editPost: (postContent: PostLayoutProps, postID: string) => { },
          deletePost: (postID: string) => { },
        };
        // Check if auth.user and auth.user.author are defined before comparing IDs

        if (auth.user && auth.user.author && respPost.author.id === auth.user.author.id) {

          post.isEditable = true;
          post.editPost = editPostFunction;
          post.deletePost = deletePostFunction;
        } else {
          post.isEditable = false;
        }

        fetchedPosts.push(post);
      }

      setPosts(fetchedPosts); // Update posts state with the mapped posts
    } catch (error) {
      console.error('Failed to fetch author posts:', error);
      setPageNumber(1); // Decrement the page number if there's an error (only if page is not 1)
    }
  };

  useEffect(() => {
    const fetchAuthorData = async () => {
      const queryString = window.location.search;
      const params = new URLSearchParams(queryString);
      const idValue = params.get('id');
      const postID = params.get('post');


      setUrlId(idValue || "");
      if (idValue) {
        try {

          const response = await axios.get(`/api/authors/${idValue}?all`);
          setAuthor(response.data);
          // console.log(response.data);
          getPostsOnPage(1, idValue); // Pass the author ID directly

          getAuthorFollowers(idValue).then((followers) => {
            setFollowerCount(followers.length);
          });

        } catch (error) {
          console.error('Failed to fetch author data:', error);
          history('/');
        }
      } else {
        history('/');
      }


      if (postID) {
        const response = await axios.get(`/api/authors/${idValue}/posts/${postID}?all`);
        setCurrentPost(response.data);
        setPostShown(true);
      }
    };
    const cookiesAuth = Cookies.get('auth');
    // console.log('cookies', cookiesAuth);
    // check if the user is logged in
    if (!auth.user.author) {
      // check the cookies

      if (cookiesAuth) {
        const authUser = JSON.parse(cookiesAuth);
        // console.log('cookies', authUser);
        auth.setUser(authUser);
        setIsUserLoggedIn(true);
      }

    } else {
      setIsUserLoggedIn(true);
    }

    fetchAuthorData();


  }, [history, auth.user]);

  useEffect(() => {
    async function fetchPosts() {
      await getPostsOnPage(pageNumber, urlId);
    }

    if (fetchNewItems) {
      fetchPosts();
      setFetchNewItems(false);
    }
  }, [fetchNewItems]);

  useEffect(() => {

    // if the urlId is not the logged in user, check if the logged in user is following the author
    if (!isUserLoggedIn) return;
    if (!urlId) return;
    if (!auth.user.author) return;
    if (getIdFromUrlRegex(urlId) === auth.user.author.id) return;
    isUserFollowingAuthor(urlId, auth.user).then((isFollowing) => {
      setIsUserFollowing(isFollowing);
    }
    );
  }, [isUserLoggedIn, urlId]);


  // every 60 seconds poll if the follow status has changed, only if the user sent a follow request. Once the follow request is accepted, stop polling
  useEffect(() => {
    if (isFollowPending) {
      const pollingInterval = 10000; // Poll every 30000 milliseconds (30 seconds)
      let intervalId: NodeJS.Timeout;
      intervalId = setInterval(() => {
        isUserFollowingAuthor(urlId, auth.user).then((isFollowing) => {
          if (isFollowing) {
            setIsUserFollowing(true);
            setIsFollowPending(false);
            clearInterval(intervalId);
            // increase the follower count
            setFollowerCount(followerCount + 1);
          }
        });
      }, pollingInterval);
      return () => clearInterval(intervalId); // Cleanup on unmount
    }
  }, [isFollowPending]);



  async function nextPage() {
    // Increment page number first

    await getPostsOnPage(pageNumber + 1, urlId);



    // if there is an error set the page number back to the previous value

  }

  async function previousPage() {
    // Increment page number first
    if (pageNumber === 1) {
      return;
    }
    await getPostsOnPage(pageNumber - 1, urlId);
  }

  // make a get request to get author data
  const toggleCreatePostDialog = () => {
    if (!auth.user.author) {
      // redirect to login
      history('/login');
      return;
    }
    setIsCreatePostOpen(!isCreatePostOpen);
  };

  const editPostFunction = async (postContent: PostLayoutProps, postID: string) => {
    // refresh the posts on the page
    // console.log('editing post');
    // console.log(pageNumber)
    setFetchNewItems(true);
  };

  const deletePostFunction = async (postID: string) => {
    // refresh the posts on the page
    // console.log('deleting post');
    // console.log(pageNumber)
    setFetchNewItems(true);
  };
  const addPost = async (post: PostLayoutProps) => {
    // refresh the posts on the page
    await getPostsOnPage(pageNumber, urlId);

  }

  const followAuthorOnClick = async () => {
    if (!auth.user) {
      // redirect to login
      history('/login');
      return;
    }
    if (!author) return;
    // check if the user is already following the author
    if (isUserFollowing) {

      await unFollowAuthor(author.id, auth.user, setFollowerCount);
      setIsUserFollowing(false);

    } else {
      await followAuthor(author, auth.user, setIsFollowPending);
    }

  }

  const editProfile = () => {
    history('/editprofile');
  }


  useEffect(() => {
    // console.log('useEffect');
    const pollingInterval = 10000; // Poll every 5000 milliseconds (5 seconds)
    let intervalId: NodeJS.Timeout;
    intervalId = setInterval(() => getPostsOnPage(pageNumber, urlId), pollingInterval);
    // if (activeTab === 'public') {
    //   intervalId = setInterval(fetchLatestPublicPost, pollingInterval);
    // } else if (activeTab === 'following' && auth.user && auth.user.author) {
    //   intervalId = setInterval(fetchLatestFollowingPost, pollingInterval);
    // }


    return () => clearInterval(intervalId); // Cleanup on unmount
  }, [posts]);

  return (
    <>
      {postShown && currentPost && (
        <PostViewer onClose={onPostClose} postContent={currentPost} />
      )}
      <div className="sidebar-container">
        <Sidebar onOpenCreatePost={toggleCreatePostDialog} />
      </div>
      <div className="user-outer-container">

        <div className="profile-container">
          <div className="profile-header">
            <div className="profile-image-section">
              <img src={author?.profileImage} alt="Profile Picture" />
              <h1>{author?.displayName}</h1>
            </div>
            <div className="profile-info">
              <p>{author?.github}</p>
              <p className="follower-count">Followers: {followerCount}</p>
            </div>
            <div className="follow-container">
              {author && auth.user?.author && getIdFromUrlRegex(author.id) === getIdFromUrlRegex(auth.user.author.id) ? (
                <button onClick={editProfile}>Edit Profile</button>
              ) : (

                isUserFollowing ? (
                  <button onClick={followAuthorOnClick}>Unfollow</button>
                ) : (
                  <button onClick={followAuthorOnClick}>Follow</button>
                ) && (isFollowPending ? (
                  <button disabled>Pending...</button>
                ) : (
                  <button onClick={followAuthorOnClick}>Follow</button>
                )
                )

              )}
            </div>
          </div>
        </div>


        <div className="home-container">

          <div className="main-container">
            <div className="header-container">
              <h1>Profile</h1>
            </div>
            <div className="main-content">
              <PostContainer posts={posts} nextPage={nextPage} prevPage={previousPage} />
            </div>
          </div>
        </div>

        {isCreatePostOpen && <div className="create-post-outer"> <CreatePost onClose={() => setIsCreatePostOpen(false)} postReturner={addPost} />    </div>}
      </div>

    </>
  );
}

export default UserPage;
