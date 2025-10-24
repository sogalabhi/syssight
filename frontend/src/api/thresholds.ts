import apiRequest from './client'
import type { ThresholdConfigResponse, ThresholdConfigUpdate } from '../types'

export const getThresholds = async (): Promise<ThresholdConfigResponse> => {
  return apiRequest<ThresholdConfigResponse>('/api/v1/thresholds')
}

export const updateThresholds = async (
  update: ThresholdConfigUpdate
): Promise<ThresholdConfigResponse> => {
  return apiRequest<ThresholdConfigResponse>('/api/v1/thresholds', 'PUT', update)
}

export const resetThresholds = async (): Promise<ThresholdConfigResponse> => {
  return apiRequest<ThresholdConfigResponse>('/api/v1/thresholds/reset', 'POST')
}

