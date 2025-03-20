import { NextRequest, NextResponse } from 'next/server';
import { v4 as uuidv4 } from 'uuid';
import { parseCSV } from '@/app/utils/dataProcessing';
import { convertToParquet } from '@/app/utils/parquetConverter';
import { storeData } from '@/app/utils/redisClient';

// Maximum file size (25MB)
const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB in bytes

export async function POST(request: NextRequest) {
  try {
    // Check content length header
    const contentLength = request.headers.get('content-length');
    if (contentLength && parseInt(contentLength) > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: 'File size exceeds the 25MB limit' },
        { status: 413 }
      );
    }

    // Get form data
    const formData = await request.formData();
    const file = formData.get('file') as File;

    // Validate file
    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      );
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return NextResponse.json(
        { error: 'File size exceeds the 25MB limit' },
        { status: 413 }
      );
    }

    // Check file type
    if (!file.name.endsWith('.csv')) {
      return NextResponse.json(
        { error: 'Only CSV files are supported' },
        { status: 400 }
      );
    }

    // Read file content
    const fileContent = await file.text();
    
    // Parse CSV data
    const parsedData = await parseCSV(fileContent);
    
    if (!parsedData || parsedData.length === 0) {
      return NextResponse.json(
        { error: 'No data found in the CSV file' },
        { status: 400 }
      );
    }

    // Generate a unique ID for this dataset
    const datasetId = uuidv4();
    
    try {
      // Convert to buffer format (previously Parquet)
      const dataBuffer = await convertToParquet(parsedData);
      
      // Store in Redis with buffer
      await storeData(datasetId, {
        data: parsedData,
        buffer: dataBuffer.toString('base64'), // Store buffer as base64 string
        timestamp: new Date().toISOString(),
        filename: file.name
      });
    } catch (conversionError) {
      console.error('Error in data conversion:', conversionError);
      
      // Fallback: If conversion fails, just store the parsed data
      await storeData(datasetId, {
        data: parsedData,
        timestamp: new Date().toISOString(),
        filename: file.name
      });
    }
    
    return NextResponse.json({
      success: true,
      datasetId,
      rowCount: parsedData.length,
      columns: Object.keys(parsedData[0])
    });
    
  } catch (error) {
    console.error('Error processing upload:', error);
    return NextResponse.json(
      { error: 'Failed to process the file' },
      { status: 500 }
    );
  }
} 