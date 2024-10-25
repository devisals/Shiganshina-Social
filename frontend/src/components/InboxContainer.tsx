import React, { useState, useEffect } from 'react';
import { useAuth } from './context/auth.tsx';
import Cookies from 'js-cookie';
import PostViewer from './PostViewer.tsx';
import { PostLayoutProps } from './types/PostLayoutProps.tsx';
import { acceptFollowRequest} from './types/FollowersHelper.tsx';

type InboxContainerProps = {
    inboxItems: any[]
}

const InboxContainer: React.FC<InboxContainerProps> = ({ inboxItems }) => {
    const [postShown, setPostShown] = useState(false);
    const [currentPost, setCurrentPost] = useState<PostLayoutProps | null>(null);
    const auth = useAuth();
    const [numItems , setNumItems] = useState(-1);

    useEffect(() => {
        const cookiesAuth = Cookies.get('auth');
        // console.log('cookies', cookiesAuth);
        // check if the user is logged in
        if (!auth.user.author) {
            // check the cookies
            if (cookiesAuth) {
                const authUser = JSON.parse(cookiesAuth);
                // console.log('cookies', authUser);
                auth.setUser(authUser);
            }
        }
    }, []);

    function onPostClose() {
        setPostShown(false);
        setCurrentPost(null); // Clear the current post when closing
    }

    function viewPost(item: PostLayoutProps) {
        setCurrentPost(item); // Set the current post to the one clicked
        setPostShown(true); // Show the PostViewer
    }

    const renderItem = (item: any, index: number) => {
        // You can directly use index for key if inboxItems are guaranteed to be static or ordered

        switch (item.type.toLowerCase()) {
            case "post":
                return inboxPost(item, index);
            case "follow":
                return inboxRequest(item, index);
            case "like":
                return inboxLike(item, index);
            case "comment":
                return inboxComment(item, index);
            default:
                return <div key={index}>Unknown item type</div>;
        }
    };


    function inboxPost(item: any, key:number) {
        // console.log('inbox post', item);
        return (
            <div className="inbox-post" key={key}>
                <div>A post was shared with you</div>
                <div className="post-author">Author: {item.author.displayName}</div>
                <div className="post-title">Title: {item.title}</div>
                <div className="info-blurb">Click the button below to view the post</div>
                <button onClick={() => viewPost(item)}>View Post</button>
            </div>
        );
    }

    function inboxRequest(item: any, key:number) {
        const actor = JSON.parse(JSON.stringify(item.actor))
        
        return (
            <div className="inbox-request" key={key}>
                <div className="request-summary">{item.summary}</div>
                <button onClick={() => acceptFollowRequest(actor, auth.user)}>Accept</button>
            </div>
        );
    }

    function inboxLike(item: any, key:number) {
        return (
            <div className="inbox-like" key={key}>
                <div className="request-summary">{item.summary}</div>
            </div>
        );
    }

    function inboxComment(item: any, key:number) {
        return (
            <div className="inbox-comment" key={key}>
                <div className="info-header">New Comment!</div>
                <div className="request-actor">@{item.author.displayName}</div>
                <div className="request-summary">{item.comment}</div>
            </div>
        );
    }


    return (
        <>
            <div className="inbox-container">
                {inboxItems.map(renderItem)}
            </div>
            {postShown && currentPost && (
                <PostViewer onClose={onPostClose} postContent={currentPost} />
            )}
        </>
    );
}

export default InboxContainer;
