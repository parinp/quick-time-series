import { Redis } from '@upstash/redis';

// Initialize Redis client
const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL || '',
  token: process.env.UPSTASH_REDIS_REST_TOKEN || '',
});

// Maximum chunk size (slightly less than 1MB to be safe)
const MAX_CHUNK_SIZE = 900 * 1024; // ~900KB

// Store large data by splitting it into chunks
export const storeDataChunked = async (key: string, data: any, expirationInSeconds = 3600) => {
  try {
    console.log(`Storing chunked data with key: ${key}`);
    
    // Convert data to JSON string if it's not already a string
    let jsonString;
    if (typeof data === 'string') {
      jsonString = data;
    } else {
      try {
        jsonString = JSON.stringify(data);
      } catch (stringifyError) {
        console.error('Error stringifying data:', stringifyError);
        // If we can't stringify, store as is in a single chunk
        const metadata = {
          totalChunks: 1,
          totalSize: 0,
          timestamp: new Date().toISOString()
        };
        
        console.log(`Storing metadata for key ${key}:meta:`, metadata);
        await redis.set(`${key}:meta`, JSON.stringify(metadata), { ex: expirationInSeconds });
        
        console.log(`Storing direct object for key ${key}:chunk:0`);
        await redis.set(`${key}:chunk:0`, data, { ex: expirationInSeconds });
        return true;
      }
    }
    
    // Calculate number of chunks needed
    const totalLength = jsonString.length;
    const numChunks = Math.ceil(totalLength / MAX_CHUNK_SIZE);
    
    console.log(`Data size: ${totalLength} bytes, splitting into ${numChunks} chunks`);
    
    // Store metadata
    const metadata = {
      totalChunks: numChunks,
      totalSize: totalLength,
      timestamp: new Date().toISOString()
    };
    
    console.log(`Storing metadata for key ${key}:meta:`, metadata);
    await redis.set(`${key}:meta`, JSON.stringify(metadata), { ex: expirationInSeconds });
    
    // Store each chunk
    const pipeline = redis.pipeline();
    for (let i = 0; i < numChunks; i++) {
      const start = i * MAX_CHUNK_SIZE;
      const end = Math.min(start + MAX_CHUNK_SIZE, totalLength);
      const chunk = jsonString.substring(start, end);
      
      pipeline.set(`${key}:chunk:${i}`, chunk, { ex: expirationInSeconds });
    }
    
    await pipeline.exec();
    console.log(`Successfully stored ${numChunks} chunks for key: ${key}`);
    return true;
  } catch (error) {
    console.error('Error storing chunked data in Redis:', error);
    return false;
  }
};

// Retrieve chunked data
export const retrieveDataChunked = async (key: string) => {
  try {
    console.log(`Retrieving chunked data with key: ${key}`);
    
    // Get metadata
    const metaData = await redis.get(`${key}:meta`);
    if (!metaData) {
      console.log(`No metadata found for key: ${key}`);
      return null;
    }
    
    // Parse metadata - handle both string and object formats
    let meta;
    if (typeof metaData === 'string') {
      try {
        meta = JSON.parse(metaData);
      } catch (parseError) {
        console.error('Error parsing metadata JSON:', parseError);
        console.log('Raw metadata:', metaData);
        return null;
      }
    } else {
      // If it's already an object, use it directly
      console.log('Metadata is already an object, using directly');
      meta = metaData;
    }
    
    const { totalChunks } = meta;
    
    console.log(`Found ${totalChunks} chunks for key: ${key}`);
    
    // Retrieve all chunks
    let jsonString = '';
    for (let i = 0; i < totalChunks; i++) {
      const chunk = await redis.get(`${key}:chunk:${i}`);
      if (!chunk) {
        console.log(`Missing chunk ${i} for key: ${key}`);
        return null;
      }
      
      // Make sure we're dealing with a string
      if (typeof chunk === 'string') {
        jsonString += chunk;
      } else {
        console.log(`Chunk ${i} is not a string, it's a ${typeof chunk}`);
        // If it's already an object, just return the data directly
        if (i === 0 && totalChunks === 1) {
          return chunk;
        } else {
          throw new Error(`Chunk ${i} is not a string, cannot concatenate`);
        }
      }
    }
    
    try {
      // Parse the complete JSON string
      return JSON.parse(jsonString);
    } catch (parseError) {
      console.error('Error parsing JSON string:', parseError);
      console.log('First 100 chars of jsonString:', jsonString.substring(0, 100));
      // If parsing fails but we have a single chunk that might be an object already
      if (totalChunks === 1) {
        const singleChunk = await redis.get(`${key}:chunk:0`);
        return singleChunk;
      }
      throw parseError;
    }
  } catch (error) {
    console.error('Error retrieving chunked data from Redis:', error);
    return null;
  }
};

// Store data in Redis with expiration (default 1 hour)
export const storeData = async (key: string, data: any, expirationInSeconds = 3600) => {
  try {
    console.log(`Storing data with key: ${key}`);
    
    // Try to convert to JSON string
    let jsonString;
    try {
      jsonString = JSON.stringify(data);
    } catch (stringifyError) {
      console.error('Error stringifying data:', stringifyError);
      // If we can't stringify, store as is
      console.log(`Storing data directly for key: ${key}`);
      await redis.set(key, data, { ex: expirationInSeconds });
      return true;
    }
    
    // If data is too large, use chunking
    if (jsonString.length > MAX_CHUNK_SIZE) {
      console.log(`Data size (${jsonString.length} bytes) exceeds chunk limit, using chunked storage`);
      return storeDataChunked(key, data, expirationInSeconds);
    }
    
    // Otherwise use normal storage
    console.log(`Storing JSON string for key: ${key}`);
    await redis.set(key, jsonString, { ex: expirationInSeconds });
    return true;
  } catch (error) {
    console.error('Error storing data in Redis:', error);
    return false;
  }
};

// Retrieve data from Redis
export const retrieveData = async (key: string) => {
  try {
    console.log(`Retrieving data with key: ${key}`);
    
    // First try to get metadata (to check if it's chunked)
    const metaData = await redis.get(`${key}:meta`);
    
    // If metadata exists, it's chunked data
    if (metaData) {
      console.log(`Found chunked data for key: ${key}`);
      return retrieveDataChunked(key);
    }
    
    // Otherwise try normal retrieval
    const data = await redis.get(key);
    if (!data) {
      console.log(`No data found for key: ${key}`);
      return null;
    }
    
    console.log(`Data found for key: ${key}`);
    
    // Handle both string and object data
    if (typeof data === 'string') {
      try {
        return JSON.parse(data);
      } catch (parseError) {
        console.error('Error parsing data as JSON:', parseError);
        // If it's not valid JSON, return as is
        return data;
      }
    } else {
      // If it's already an object, return as is
      return data;
    }
  } catch (error) {
    console.error('Error retrieving data from Redis:', error);
    return null;
  }
};

// Delete data from Redis (including chunks if present)
export const deleteData = async (key: string) => {
  try {
    // Check if it's chunked data
    const metaData = await redis.get(`${key}:meta`);
    
    if (metaData) {
      // It's chunked data, delete all chunks
      const meta = JSON.parse(metaData as string);
      const { totalChunks } = meta;
      
      const pipeline = redis.pipeline();
      pipeline.del(`${key}:meta`);
      
      for (let i = 0; i < totalChunks; i++) {
        pipeline.del(`${key}:chunk:${i}`);
      }
      
      await pipeline.exec();
    } else {
      // Normal data, just delete the key
      await redis.del(key);
    }
    
    return true;
  } catch (error) {
    console.error('Error deleting data from Redis:', error);
    return false;
  }
};

// Check if key exists in Redis
export const keyExists = async (key: string) => {
  try {
    // Check both normal key and metadata key
    const normalExists = await redis.exists(key);
    const metaExists = await redis.exists(`${key}:meta`);
    
    return normalExists || metaExists;
  } catch (error) {
    console.error('Error checking key in Redis:', error);
    return false;
  }
};

export default redis; 