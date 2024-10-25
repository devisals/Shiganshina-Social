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
import { backendHost, getIdFromUrlRegex } from './types/Host.tsx';
import Cookies from 'js-cookie';

const Home: React.FC = () => {
  const history = useNavigate();
  const [isCreatePostOpen, setIsCreatePostOpen] = useState(false);
  const [posts, setPosts] = useState<PostProps[]>([]);
  const auth = useAuth();
  const [pageNumber, setPageNumber] = useState(1);
  const [fetchNewItems, setFetchNewItems] = useState(true);
  const size = 15;
  const [activeTab, setActiveTab] = useState('public');


  const hostApiUrl = backendHost
  useEffect(() => {
    const cookiesAuth = Cookies.get('auth');
    // check if the user is logged in
    if (!auth.user.author) {
      // check the cookies

      if (cookiesAuth) {
        const authUser = JSON.parse(cookiesAuth);
        auth.setUser(authUser);
      }
    }

  }, [auth]);

  useEffect(() => {
    async function fetchPosts() {
      await getPostsOnPage(pageNumber);
    }

    if (fetchNewItems) {
      fetchPosts();
      setFetchNewItems(false);
    }
  }, [fetchNewItems]);

  useEffect(() => {
    const pollingInterval = 10000; // Poll every 5000 milliseconds (5 seconds)
    let intervalId: NodeJS.Timeout;
    intervalId = setInterval(() => getPostsOnPage(pageNumber), pollingInterval);
    // if (activeTab === 'public') {
    //   intervalId = setInterval(fetchLatestPublicPost, pollingInterval);
    // } else if (activeTab === 'following' && auth.user && auth.user.author) {
    //   intervalId = setInterval(fetchLatestFollowingPost, pollingInterval);
    // }


    return () => clearInterval(intervalId); // Cleanup on unmount
  }, [posts]); // Dependency array includes posts to ensure updates are based on the latest state



  const getPostsOnPage = async (pageNumber: number): Promise<void> => {
    setPageNumber(pageNumber);
    let headers = {}

    let apiUrl = `/api/authors/test/posts/public?page=${pageNumber}&size=${size}&all`; // Default to public posts
    headers = {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${auth.user.token}`
    };

    if (activeTab === 'following') {
      if (!auth.user || !auth.user.author) {
        history('/login');
        return;
      }
      apiUrl = `/api/authors/${getIdFromUrlRegex(auth.user.author.id)}/posts/following?page=${pageNumber}&size=${size}&all`;

    }

    try {
      let response;
      if (activeTab === 'public') {
        response = await axios.get(apiUrl);
      } else {
        response = await axios.get(apiUrl, { headers });
      }

      // update the github posts
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
      // clear the posts
      setPosts([]);
      // set the old posts
      setPageNumber(1);
    }
  };



  async function nextPage() {
    // Increment page number first

    await getPostsOnPage(pageNumber + 1);



    // if there is an error set the page number back to the previous value

  }

  async function previousPage() {
    // Increment page number first
    if (pageNumber === 1) {
      return;
    }
    await getPostsOnPage(pageNumber - 1);
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
    setFetchNewItems(true);
  };

  const deletePostFunction = async (postID: string) => {
    // refresh the posts on the page
    setFetchNewItems(true);
  };
  const addPost = async (post: PostLayoutProps) => {
    // refresh the posts on the page
    await getPostsOnPage(pageNumber);

  }

  async function switchActiveTab(tab: string) {
    setPageNumber(1);
    setActiveTab(tab);
    setFetchNewItems(true);
  }


  return (
    <>
      <div className="sidebar-container">
        <Sidebar onOpenCreatePost={toggleCreatePostDialog} />
      </div>
      <div className="user-outer-container">
        <div className="tabs-container">
          <button
            className={`tab ${activeTab === 'public' ? 'active' : ''}`}
            onClick={() => switchActiveTab('public')}
          >
            Public Posts
          </button>
          <button
            className={`tab ${activeTab === 'following' ? 'active' : ''}`}
            onClick={() => switchActiveTab('following')}
          >
            Friends & Following Posts
          </button>
        </div>

        <div className="home-container">

          <div className="main-container">
            <div className="header-container">
              <h1>Home</h1>
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

export default Home;
