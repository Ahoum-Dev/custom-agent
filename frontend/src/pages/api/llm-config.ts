import type { NextApiRequest, NextApiResponse } from 'next';
import * as fs from 'fs';
import * as path from 'path';
import { LLMConfig } from '@/lib/types';

type ApiResponse = {
  success: boolean;
  message: string;
  data?: LLMConfig | LLMConfig[];
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse>
) {
  if (req.method === 'POST') {
    try {
      const config = req.body as LLMConfig;
      
      // Validate config
      if (!config.name) {
        return res.status(400).json({ success: false, message: 'Name is required' });
      }

      // Create directory if it doesn't exist
      const configDir = path.join(process.cwd(), 'configs');
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }

      // Save config to file
      const filePath = path.join(configDir, `${config.name.replace(/\s+/g, '-').toLowerCase()}.json`);
      fs.writeFileSync(filePath, JSON.stringify(config, null, 2));

      return res.status(200).json({ 
        success: true, 
        message: 'Configuration saved successfully',
        data: config
      });
    } catch (error) {
      console.error('Error saving configuration:', error);
      return res.status(500).json({ 
        success: false, 
        message: 'Failed to save configuration'
      });
    }
  } else if (req.method === 'GET') {
    try {
      const configDir = path.join(process.cwd(), 'configs');
      
      // If config directory doesn't exist, create it
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
        return res.status(200).json({ success: true, message: 'No configurations found', data: [] });
      }
      
      // Check if a specific configuration is requested
      const { name } = req.query;
      
      if (name && typeof name === 'string') {
        const fileName = `${name.replace(/\s+/g, '-').toLowerCase()}.json`;
        const filePath = path.join(configDir, fileName);
        
        if (!fs.existsSync(filePath)) {
          return res.status(404).json({ success: false, message: 'Configuration not found' });
        }
        
        const configData = fs.readFileSync(filePath, 'utf8');
        const config = JSON.parse(configData) as LLMConfig;
        
        return res.status(200).json({
          success: true,
          message: 'Configuration loaded successfully',
          data: config
        });
      }
      
      // Otherwise return list of all configurations
      const files = fs.readdirSync(configDir).filter(file => file.endsWith('.json'));
      const configs = files.map(file => {
        const filePath = path.join(configDir, file);
        const configData = fs.readFileSync(filePath, 'utf8');
        return JSON.parse(configData) as LLMConfig;
      });
      
      return res.status(200).json({
        success: true,
        message: 'Configurations loaded successfully',
        data: configs
      });
    } catch (error) {
      console.error('Error loading configurations:', error);
      return res.status(500).json({
        success: false,
        message: 'Failed to load configurations'
      });
    }
  } else {
    return res.status(405).json({ success: false, message: 'Method not allowed' });
  }
} 