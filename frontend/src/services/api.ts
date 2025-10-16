import axios from 'axios';
import { Region } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const api = {
  async getRegions(): Promise<Region[]> {
    const response = await axios.get(`${API_BASE_URL}/api/regions`);
    return response.data.regions;
  },

  async generateRoute(region: Region): Promise<any> {
    const response = await axios.post(`${API_BASE_URL}/api/regions/${region.id}/routes`, {}, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  },

  async getRouteStatus(region: Region, jobId: string): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/api/regions/${region.id}/routes/${jobId}`);
    return response.data;
  },
};

