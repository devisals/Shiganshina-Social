import React from "react";
import "./Sidebar.css";
import { SidebarData } from "./SidebarData";
import { SidebarItem } from "./types/SiderbarItem.tsx"; // Assuming you create a types.ts for custom types
import { SidebarProps } from "./types/SidebarProps.tsx";
import { Create, Key } from "@mui/icons-material";
import PersonIcon from "@mui/icons-material/Person";
import { useAuth, AuthUser } from "./context/auth.tsx";
import { useNavigate } from "react-router-dom";
import { backendHost, getIdFromUrlRegex } from "./types/Host.tsx";
import Cookies from 'js-cookie';
const Sidebar: React.FC<SidebarProps> = ({ onOpenCreatePost }) => {
  const auth = useAuth();
  const history = useNavigate();

  const redirectToPersonalProfile = () => {
    if (!auth.user.author) {
      const authString = Cookies.get('auth');
      if (!authString) {
        history('/login');
        return;
      }
      auth.setUser(JSON.parse(authString));
    }

    const authorId = getIdFromUrlRegex(auth.user.author.id);
    history('/profile?id=' + authorId);
  }

  function signOut() {
    const isConfirmed = window.confirm("Are you sure you want to sign out?");
    if (!isConfirmed) {
      return; // Stop here if the user cancels the action
    }

    // Proceed with sign out if confirmed
    auth.setUser({} as AuthUser);
    Cookies.remove('auth');
    history('/');
  }



  function isUserSignedIn() {
    if (auth.user.author) {
      return true;
    }

    const authString = Cookies.get('auth');
    if (authString) {
      const parsed = JSON.parse(authString);
      auth.setUser(parsed);
      return true;
    }
    return false;
  }

  const redirectToLogin = () => {
    history('/login');
  }

  const redirectToSignUp = () => {
    history('/signup');
  }

  return (
    <div className="Sidebar">
      <div className="logo-outer"><h1 className="logo"></h1></div>
      <ul className="SidebarList">
        {SidebarData.filter((val: SidebarItem) => {
          // Exclude "Notifications" if user is not signed in
          return isUserSignedIn() || val.title !== "Inbox";
        }).map((val: SidebarItem, key: number) => {
          return (
            <li
              key={key}
              className="row"
              id={window.location.pathname === val.link ? "active" : ""}
              onClick={() => {
                history(val.link);
              }}
            >
              <div id="icon">{val.icon}</div>
              <div id="title">{val.title}</div>
            </li>
          );
        })}


        {isUserSignedIn() &&
          <>
            <li className="row create-post" onClick={onOpenCreatePost}>
              <div id="icon"><Create></Create></div>
              <div id="title">Create Post</div>
            </li>
            <li className="row profile" onClick={redirectToPersonalProfile}>
              <div id="icon"><PersonIcon /></div>
              <div id="title">Profile</div>
            </li>
          </>}

        {!isUserSignedIn() && <><li className="row profile" onClick={redirectToLogin}>

          <div id="icon"><PersonIcon /></div>
          <div id="title">Login</div>
        </li>
          <li className="row profile" onClick={redirectToSignUp}>
            <div id="icon"><Key /></div>
            <div id="title">Sign Up</div>
          </li>
        </>}

        {/* only show if user is signed in */}
        {isUserSignedIn() && <li className="row sign-out" onClick={signOut}>
          <div id="icon"><Key /></div>
          <div id="title">Sign Out</div>
        </li>}

      </ul>
    </div>
  );
}

export default Sidebar;
