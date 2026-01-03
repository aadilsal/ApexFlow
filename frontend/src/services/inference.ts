import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_APEX_API_KEY || 'race-weekend-key-2026';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'X-Apex-Key': API_KEY,
        'Content-Type': 'application/json',
    },
});

export interface PredictionRequest {
    driver_id: string;
    circuit_id: string;
    fuel_load: number;
    track_temp: number;
    session_type: string;
    tire_compound: string;
}

export interface PredictionResponse {
    predicted_lap_time: number;
    confidence_interval: {
        lower_bound: number;
        upper_bound: number;
    };
    model_version: string;
    inference_time_ms: number;
}

export const inferenceService = {
    predict: async (data: PredictionRequest): Promise<PredictionResponse> => {
        const response = await apiClient.post<PredictionResponse>('/v1/predict', data);
        return response.data;
    },
    health: async () => {
        const response = await apiClient.get('/health');
        return response.data;
    }
};
