import React from "react";
import HomeIcon from "@mui/icons-material/Home";
import SearchIcon from "@mui/icons-material/Search";
import PostAddIcon from "@mui/icons-material/PostAdd";
import NotificationsIcon from "@mui/icons-material/Notifications";
import PersonIcon from "@mui/icons-material/Person";


interface SidebarItem {
  title: string;
  icon: JSX.Element;
  link: string;
}

export const SidebarData: SidebarItem[] = [
  {
    title: "Home",
    icon: <HomeIcon />,
    link: "/",
  },
  {
    title: "Search",
    icon: <SearchIcon />,
    link: "/search",
  },
  {
    title: "Inbox",
    icon: <NotificationsIcon />,
    link: "/inbox",
  },
];

export default SidebarData;
