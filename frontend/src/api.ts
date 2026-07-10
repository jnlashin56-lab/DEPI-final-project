import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

export interface ItineraryStop {
  place_id: number;
  name: string;
  name_ar?: string;
  category: string;
  description: string;
  price_egp?: number;
  predicted_crowd: string;
  crowd_score: number;
  story: string;
  day?: number;
}

export interface RecommendationResponse {
  itinerary: ItineraryStop[];
}

export const recommendItinerary = async (userInput: string): Promise<RecommendationResponse> => {
  const response = await axios.post<RecommendationResponse>(`${API_BASE}/recommend`, {
    user_input: userInput
  });
  return response.data;
};

export const chatBooking = async (userInput: string) => {
  const response = await axios.post(`${API_BASE}/chat/booking`, {
    user_input: userInput
  });
  return response.data;
};
