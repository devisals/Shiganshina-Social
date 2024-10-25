// import process from "process";
// // console.log(process.env)
// const apiUrl = process.env.HOST_API_URL.replace('/api','/');

// console.log('full vite environment:', import.meta.env)
const apiUrl = import.meta.env.VITE_HOST_BACKEND;
// console.log('apiURL', apiUrl);
export const backendHost2 = "http://127.0.0.1:8000/";
export const backendHost = apiUrl;

export const getIdFromUrlRegex = (url: string | undefined): string | undefined => {
  if (!url) {
    return undefined;
  }
  // if it just a number return it
  // console.log(url);
  if (!isNaN(parseFloat(url))) {
    return url;
  }

  const parts = url.split('/');

  return parts[parts.length - 1];
};



