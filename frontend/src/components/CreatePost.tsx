import React, { useState, useEffect } from 'react';
import './CreatePost.css';
import { CreatePostProps } from './types/CreatePostProps.tsx'; // Assuming you create a types.ts for custom types
import { useAuth } from './context/auth.tsx';
import { PostLayoutProps } from './types/PostLayoutProps.tsx';
import axios from 'axios';
import { backendHost, getIdFromUrlRegex } from './types/Host.tsx';
import imageCompression from 'browser-image-compression';

// Modify the function component to accept all the props from CreatePostProps
const CreatePost: React.FC<CreatePostProps> = ({ onClose, postReturner, postID: postID = '',
  post: postContent = {
    type: "post",
    title: "",
    id: "",
    source: window.location.href, // current url
    origin: window.location.href, // current url
    description: "",
    contentType: "",
    content: "",
    author: {
      id: "",
      displayName: "",
      github: "",
      url: "",
      host: "",
      profileImage: ""
    }, // Providing a default Author structure
    count: 0,
    comments: "",
    published: "",
    visibility: "PUBLIC" // Assuming a default visibility, adjust as needed

  },
  isEdit = false// Default to false

}) => {

  const [title, setTitle] = useState(postContent?.title || '');
  const [description, setDescription] = useState(postContent?.description || '');
  const [text, setText] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const [currVisibility, setVisibility] = useState<string>(postContent.visibility); // State to toggle visibility
  const [currContentType, setContentType] = useState<string>(postContent.contentType); // State to toggle content type
  const [postTypeInfo, setPostTypeInfo] = useState<string>("You are creating a Text post");
  const [forceMarkdown, setForceMarkdown] = useState<boolean>(false);
  const [isImagePost, setIsImagePost] = useState<boolean>(false);
  const [imageType, setImageType] = useState<string>(""); // State to store the image type
  const auth = useAuth();
  const [imageChanged, setImageChanged] = useState(false);




  useEffect(() => {
    if (isEdit) {
      if (postContent.contentType === "text/markdown" || postContent.contentType === "text/plain") {
        setText(postContent.content);
      } else {
        setImages([postContent.content]);
      }
    }
  }, []);

  //TODO make image posts work
  useEffect(() => {

    // Determine the content type based on the inputs
    if (forceMarkdown || text && images.length > 0) {
      setContentType("text/markdown");
      setPostTypeInfo(`You are creating a Markdown post with ${images.length} image(s)`);
    } else if (images.length === 1) {
      setPostTypeInfo("You are creating an Image post");
    } else if (images.length > 1) {
      setContentType("text/markdown");
      setPostTypeInfo(`You are creating a Markdown post with ${images.length} images`);
    } else if (text) {
      setContentType("text/plain");
      setPostTypeInfo("You are creating a Text post");
    }

    if (images.length > 0) {
      setIsImagePost(true);
    } else {
      setIsImagePost(false);
    }
  }, [text, images, forceMarkdown]);
  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
  
      // Confirm before clearing text
      if (text.trim().length > 0) {
        const isConfirmed = window.confirm("Uploading an image will remove any text content.");
        if (!isConfirmed) {
          // remove the file from the input
          event.target.value = "";
          return; // Stop here if the user cancels the action
        }
      }
  
      // Initialize FileReader to read the file
      const reader = new FileReader();
  
      // Compression options
      const options = {
        maxSizeMB: 3, // (3MB)
        maxWidthOrHeight: 1920, // compress the image if it's wider or taller than this value
        useWebWorker: true,
      };
  
      try {
        // only compress if not gif image
        let compressedFile = file;

        if (file.type !== 'image/gif'){
          compressedFile  = await imageCompression(file, options);
        }
  
  
        reader.onload = (e: any) => {
          // On load, set the result (base64 string) to images state
          const base64 = e.target.result;
          setImages([base64]); // This will be an array of base64 strings
          setText(''); // Clear existing text
          setIsImagePost(true); // Disable text input
          // set the image type 
          const type = compressedFile.type;

          setContentType(type + ';base64');
          setImageChanged(true);
        };
  
        reader.readAsDataURL(compressedFile); // Read the compressed file as Data URL (base64)
      } catch (error) {
        console.error('Error while compressing the image:', error);
        alert('There was an error compressing the image. Please try again.');
      }
    }
  };
  


  const handleVisibilityChange = (event: React.ChangeEvent<HTMLSelectElement>): void => {
    const newVisibility = event.target.value;
    setVisibility(newVisibility);
    // Optionally, update the backend or perform other actions here
  };

  function refinePostContent(content: PostLayoutProps) {
    // include only title, source, origin, description, contentType, content, visibility
    // for author make the id "https://127.0.0.1:8000/authors/" + auth.user.id if it isn't already (sometimes id maybe just the id)
    const refinedPost = {
      title: content.title,
      source: content.source,
      origin: content.origin,
      description: content.description,
      contentType: content.contentType,
      content: content.content,
      visibility: content.visibility
    }

    return refinedPost;

  }

  function previewImage(){
    if (images.length > 0){
      const imgSrc = images[0].startsWith('data:image') ? images[0] : `data:image/png;base64,${images[0]}`
      return <img src={imgSrc} alt="preview" className="preview-image" />
    }
    return "";
  }
  const handleSubmit = async (event: React.FormEvent) => {
    let uploadContent = "null";
    event.preventDefault();
    // Check if any of the required fields are empty
    if (!title.trim() || !description.trim() || (!text.trim() && images.length === 0)) {
      alert('Please fill in all fields.'); // This is a simple alert; you might want to use a more user-friendly notification system
      return;
    }

    // if there is more than 1 image or both images and text, then make it markdown 
    // if (images.length > 1 || images.length > 0 && text) {
    //   setContentType("text/markdown");
    //   // make a function to translate into markdown 
    //   uploadContent = text + "\n" + images.map((image) => `![Image](${image})`).join("\n") + "\n";
    // } else 
    if (images.length === 1) {
      let type_image = "";
      if (imageChanged){
      type_image = images[0].split(',')[0].split(':')[1];
      const image_base64 = images[0].split(',')[1];
      uploadContent = image_base64;
      } else{
        type_image = postContent.contentType;
        uploadContent = postContent.content;
      }
      // type_image += ';base64';

      setContentType(type_image);
      setIsImagePost(true);
    } else if (text) {
      uploadContent = text;
    } else if (forceMarkdown) {
      setContentType("text/markdown");
      uploadContent = text;
    }

    // if it is edit mode, make a PUT request to update the post
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${auth.user.token}`
    };

    const refinedAuthorID = getIdFromUrlRegex(auth.user.author.id);



    if (isEdit) {
      // Make a PUT request to update the post
      // Use the postID to update the post
      // Use the updated post content to update the post
      // Close the modal after updating the post

      
        
      const post = {
        author: auth.user.author,
        type: "post",
        title,
        id: postID,
        source: window.location.href, // current url
        origin: window.location.href,
        description,
        contentType: currContentType,
        content: uploadContent,
        comments: postContent.comments,
        count: postContent.count,
        published: postContent.published,
        visibility: currVisibility
      };

      const refinedPostID = getIdFromUrlRegex(post.id);
      // make a PUT request to update the post
      const refinedPost = refinePostContent(post);

      try {
        const response = await axios.put(`/api/authors/${refinedAuthorID}/posts/${refinedPostID}?all`, refinedPost, { headers })
        await postReturner(post);
        onClose();
      } catch {
        alert("Error updating the post");
      }



      return;
    }
    const post = {
      author: auth.user.author,
      type: "post",
      title,
      id: postID,
      source: window.location.href, // current url
      origin: window.location.href,
      description,
      contentType: currContentType,
      content: uploadContent,
      comments: "",
      count: 0,
      published: "",
      visibility: currVisibility
    };
    postReturner(post);
    const refinedPost = refinePostContent(post);

    onClose();
    try {
      const response = await axios.post(`/api/authors/${refinedAuthorID}/posts?all`, refinedPost, { headers })

      await postReturner(post);
      onClose();
    } catch {
      alert("Error creating the post");
    }
    return;
  };

  return (
    <div className="create-post-container">
      <form onSubmit={handleSubmit} className="create-post-form">
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="input-title"
        />
        <input
          type="text"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="input-description"
        />
        {!isImagePost &&
          <textarea
            placeholder="What's happening?"
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="input-text"
          ></textarea>
        }
        <input
          type="file"
          accept="image/png, image/jpeg, image/gif, image/bmp"
          onChange={handleImageUpload}
          className="input-file"
        />

        <div className="preview-images">
          {previewImage()}
        </div>
        <div className="visibility-dropdown">
          <label htmlFor="visibility-select">Visibility:</label>
          <select
            id="visibility-select"
            value={currVisibility}
            onChange={handleVisibilityChange}
          >
            <option value="PUBLIC">Public</option>
            <option value="UNLISTED">Unlisted</option>
            <option value="FRIENDS">Friends</option>
          </select>
        </div>
        {!isImagePost &&
          <label className='markdown-check'>
            <input
              type="checkbox"
              checked={forceMarkdown}
              onChange={(e) => setForceMarkdown(e.target.checked)}
            />
            Force Markdown
          </label>
        }
        <div className="post-type-info">This post will be saved as: {postTypeInfo}</div>
        <button type="submit" className="submit-post">Post</button>
        <button type="button" onClick={onClose} className="close-button">Close</button> {/* Close button */}
      </form>
    </div>
  );
};

export default CreatePost;
