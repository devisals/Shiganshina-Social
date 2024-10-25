import axios from 'axios';
import { Author } from './Author';
import { getIdFromUrlRegex } from './Host';
import { AuthUser } from '../context/auth';

async function followAuthor(author: Author, user: AuthUser, isFollowPending: React.Dispatch<React.SetStateAction<boolean>>) {
  if (!user) return;
  if (!user.author) {
    alert('You are not logged in');
    return;
  }
  // console.log('following author');
  // console.log(user);
  const followerURL = user.author.url
  // percent encode the url
  const encodedFollowerURL = await encodeURIComponent(followerURL);
  const refinedAuthorID = getIdFromUrlRegex(author.id);
  const refinedUserID = getIdFromUrlRegex(user.author.id);

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Basic ${user.token}`
  };

  /*
  {
    "type": "Follow",      
    "summary":"Greg wants to follow Lara",
    "actor":{
        "type":"author",
        "id":"http://127.0.0.1:5454/authors/1d698d25ff008f7538453c120f581471",
        "url":"http://127.0.0.1:5454/authors/1d698d25ff008f7538453c120f581471",
        "host":"http://127.0.0.1:5454/",
        "displayName":"Greg Johnson",
        "github": "http://github.com/gjohnson",
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
    },
    "object":{
        "type":"author",
        // ID of the Author
        "id":"http://127.0.0.1:5454/authors/9de17f29c12e8f97bcbbd34cc908f1baba40658e",
        // the home host of the author
        "host":"http://127.0.0.1:5454/",
        // the display name of the author
        "displayName":"Lara Croft",
        // url to the authors profile
        "url":"http://127.0.0.1:5454/authors/9de17f29c12e8f97bcbbd34cc908f1baba40658e",
        // HATEOS url for Github API
        "github": "http://github.com/laracroft",
        // Image from a public domain
        "profileImage": "https://i.imgur.com/k7XVwpB.jpeg"
    }
}

  */

  const inboxFollow = {
    "type": "Follow",
    "summary": `${user.author.displayName} wants to follow ${author.displayName}`,
    "actor": user.author,
    "object": author
  };

  const inboxObject = {
    type: "inbox",
    author: author.id,
    items: [inboxFollow]
  }

  // console.log('inboxFollow', inboxFollow);
  try {
    const response = await axios.post(`/api/authors/${refinedAuthorID}/inbox?all`, inboxObject, { headers });
    // console.log('follow response', response);
    isFollowPending(true);
  } catch (error) {
    console.error('Failed to follow author:', error);
  }
}



const getAuthorFollowers = async (authorID: string): Promise<Author[]> => {
  try {
    // console.log('getting followers', authorID);
    const response = await axios.get(`/api/authors/${authorID}/followers?all`);
    return response.data.items;
  } catch (error) {
    console.error('Failed to get followers:', error);
    return [];
  }
}

const getAuthorFollowing = async (authorID: string): Promise<Author[]> => {
  // check if authorID is following any authors and get them
  try {
    const refinedAuthorFollowerID = getIdFromUrlRegex(authorID);
    const encodedFollowerURL = encodeURIComponent(`/api/authors/${refinedAuthorFollowerID}`);
    const authorResponse = await axios.get(`/api/authors?all`);
    const authors = authorResponse.data.items;
    const following: Author[] = [];
    for (const author of authors) {
      const refinedAuthorID = getIdFromUrlRegex(author.id);
      try {
        const response = await axios.get(`/api/authors/${refinedAuthorID}/followers/${refinedAuthorFollowerID}?all`);
        if (response.data) {
          following.push(author);
        }
      }
      catch (error: any) {
        if (error.response.status !== 404) {
          console.error('Failed to get following:', error);
        }
      }


    }
    return following;

  } catch (error) {
    console.error('Failed to get following:', error);
    return [];
  }
}

async function unFollowAuthor(authorID: string, user: AuthUser, setFollowers: React.Dispatch<React.SetStateAction<number>>) {
  if (!user) return;
  // console.log('following author');
  const followerURL = user.author.url
  // percent encode the url
  const encodedFollowerURL = await encodeURIComponent(followerURL);
  const refinedAuthorID = getIdFromUrlRegex(authorID);
  const refinedUserID = getIdFromUrlRegex(user.author.id);
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Basic ${user.token}`
  };

  try {
    const response = axios.delete(`/api/authors/${refinedAuthorID}/followers/${encodedFollowerURL}`);
    // console.log('follow response', response);
    setFollowers((prev) => prev - 1);
  } catch (error) {
    console.error('Failed to follow author:', error);
  }
}

async function isUserFollowingAuthor(authorID: string | null, user: AuthUser): Promise<boolean> {
  if (!user) return false;
  if (!authorID) return false;
  const followerURL = user.author.url
  // percent encode the url
  const encodedFollowerURL = encodeURIComponent(followerURL);
  // console.log('encodedshit', encodedFollowerURL);
  const refinedAuthorID = getIdFromUrlRegex(authorID);
  const refinedUserID = getIdFromUrlRegex(user.author.id);
  try {
    const response = await axios.get(`/api/authors/${refinedAuthorID}/followers/${encodedFollowerURL}?all`);
    return response.data ? true : false;
  } catch (error:any) {
    console.log(error.response.data)
    return false;
  }
}

async function getAuthorFriends(authorID: string): Promise<Author[]> {
  // if both the authors are following each other, they are friends
  try {
    const authorFollowers = await getAuthorFollowers(authorID);
    const authorFollowing = await getAuthorFollowing(authorID);
    const friends: Author[] = [];
    for (const author of authorFollowers) {
      if (authorFollowing.includes(author)) {
        friends.push(author);
      }
    }
    return friends;
  } catch (error) {
    console.error('Failed to get friends:', error);
    return [];
  }
}

// async function acceptFollowRequest(authUser: AuthUser, actorID: string) {
//     if (!authUser) return;
//     // console.log('following author');
//     // console.log(authUser);
//     const authUserIDRefined = getIdFromUrlRegex(authUser.author.id);
//     const actorIDRefined = getIdFromUrlRegex(actorID);
//     const headers = {
//       'Content-Type': 'application/json',
//       'Authorization': `Basic ${authUser.token}`
//     };

//     try {
//       const response = axios.put(`/api/authors/${actorIDRefined}/followers/${authUserIDRefined}`, {headers});
//       // console.log('follow response', response);

//     } catch (error) {
//       console.error('Failed to follow author:', error);
//     }
//   }

async function acceptFollowRequest(actor: any, user: AuthUser) {

  if (!user) return;
  // console.log('following author');
  // console.log(user);
  const followerURL = actor.url
  // percent encode the url
  // console.log('actor in side functioon', actor);
  const encodedFollowerURL = encodeURIComponent(followerURL);
  const refinedAuthorID = getIdFromUrlRegex(user.author.id);

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Basic ${user.token}`
  };

  try {
    const response = await axios.put(`/api/authors/${refinedAuthorID}/followers/${encodedFollowerURL}`, {}, { headers });
    // console.log('follow response', response);
  } catch (error: any) {
    if (error.response.status === 400) {
      alert('This author is already following you');
    } else {
      console.error('Failed to follow author:', error);
    }
  }
}


export { getAuthorFollowers, followAuthor, getAuthorFollowing, unFollowAuthor, isUserFollowingAuthor, getAuthorFriends, acceptFollowRequest };


