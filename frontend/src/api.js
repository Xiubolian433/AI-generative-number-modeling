// import axios from "axios";
//
// // 创建一个 Axios 实例
// const API = axios.create({
//   baseURL: "http://127.0.0.1:5000", // Flask 后端地址
// });
//
// // 调用后端生成数字的函数
// export const fetchGeneratedNumbers = async (batchSize = 1) => {
//   try {
//     const response = await API.post("/generate", { batch_size: batchSize });
//     return response.data.results;
//   } catch (error) {
//     console.error("Error fetching generated numbers:", error);
//     throw error;
//   }
// };


import axios from "axios";

export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

const API = axios.create({
  baseURL: API_BASE_URL
});


// 动态调用后端生成数字的函数
export const fetchGeneratedNumbers = async (lotteryType = "mega_millions", batchSize = 1) => {
  try {
    const endpoint = lotteryType === "power_ball" ? "/generate/power_ball" : "/generate/mega_millions";
    const response = await API.get(endpoint, { params: { batch_size: batchSize } });
    console.log("Response data:", response.data.results); // 打印返回值
    return response.data.results;
  } catch (error) {
    console.error("Error fetching generated numbers:", error);
    throw error;
  }
};

export { API }
