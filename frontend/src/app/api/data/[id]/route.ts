import { NextRequest, NextResponse } from 'next/server';
import { retrieveData } from '@/app/utils/redisClient';
import { parseParquetBuffer } from '@/app/utils/parquetConverter';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const datasetId = params.id;
    
    if (!datasetId) {
      return NextResponse.json(
        { error: 'Dataset ID is required' },
        { status: 400 }
      );
    }
    
    console.log(`API: Retrieving data for dataset ID: ${datasetId}`);
    
    // Retrieve data from Redis
    let cachedData;
    try {
      cachedData = await retrieveData(datasetId);
    } catch (retrieveError) {
      console.error('Error retrieving data from Redis:', retrieveError);
      return NextResponse.json(
        { 
          error: 'Failed to retrieve data from cache',
          details: retrieveError instanceof Error ? retrieveError.message : 'Unknown error',
          stack: retrieveError instanceof Error ? retrieveError.stack : undefined
        },
        { status: 500 }
      );
    }
    
    if (!cachedData) {
      console.log(`API: No data found for dataset ID: ${datasetId}`);
      return NextResponse.json(
        { error: 'Dataset not found' },
        { status: 404 }
      );
    }
    
    console.log(`API: Data found for dataset ID: ${datasetId}`);
    console.log(`API: Data type: ${typeof cachedData}`);
    console.log(`API: Is array: ${Array.isArray(cachedData)}`);
    
    if (typeof cachedData === 'object') {
      console.log(`API: Data keys: ${Object.keys(cachedData).join(', ')}`);
    }
    
    // Ensure we have the data property
    let responseData;
    
    if (!cachedData.data) {
      // If the entire object is the data array
      if (Array.isArray(cachedData)) {
        console.log(`API: Returning array data directly, length: ${cachedData.length}`);
        responseData = cachedData;
      } else {
        return NextResponse.json(
          { 
            error: 'Invalid data format in cache',
            dataType: typeof cachedData,
            isArray: Array.isArray(cachedData),
            dataKeys: typeof cachedData === 'object' ? Object.keys(cachedData) : undefined
          },
          { status: 500 }
        );
      }
    } else {
      // Use the data property
      responseData = cachedData.data;
    }
    
    // Ensure responseData is an array
    if (!Array.isArray(responseData)) {
      console.error('API: responseData is not an array:', responseData);
      return NextResponse.json(
        { 
          error: 'Data is not in array format',
          dataType: typeof responseData
        },
        { status: 500 }
      );
    }
    
    console.log(`API: Returning data with ${responseData.length} rows`);
    if (responseData.length > 0) {
      console.log('API: First row sample:', responseData[0]);
    }
    
    // Return the data
    return NextResponse.json({
      success: true,
      data: responseData,
      timestamp: cachedData.timestamp || new Date().toISOString(),
      filename: cachedData.filename || 'unknown.csv'
    });
    
  } catch (error) {
    console.error('Error retrieving data:', error);
    return NextResponse.json(
      { 
        error: 'Failed to retrieve the data',
        details: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      },
      { status: 500 }
    );
  }
} 