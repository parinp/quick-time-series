import { NextRequest, NextResponse } from 'next/server';
import redis, { storeData, retrieveData } from '@/app/utils/redisClient';

export async function GET(request: NextRequest) {
  try {
    // Check if Redis URL and token are set
    const redisUrl = process.env.UPSTASH_REDIS_REST_URL;
    const redisToken = process.env.UPSTASH_REDIS_REST_TOKEN;
    
    if (!redisUrl || !redisToken) {
      return NextResponse.json({
        success: false,
        error: 'Redis credentials are not set',
        redisUrlSet: !!redisUrl,
        redisTokenSet: !!redisToken
      });
    }
    
    // Try to ping Redis
    let pingResult;
    try {
      pingResult = await redis.ping();
    } catch (pingError) {
      return NextResponse.json({
        success: false,
        error: pingError instanceof Error ? pingError.message : 'Unknown ping error',
        redisUrlSet: true,
        redisTokenSet: true
      });
    }
    
    // Try to store and retrieve a small test value
    const testKey = `test-${Date.now()}`;
    const testValue = { test: true, timestamp: new Date().toISOString() };
    
    let storeResult;
    try {
      storeResult = await storeData(testKey, testValue);
    } catch (storeError) {
      return NextResponse.json({
        success: false,
        ping: pingResult,
        error: `Store error: ${storeError instanceof Error ? storeError.message : 'Unknown store error'}`,
        redisUrlSet: true,
        redisTokenSet: true
      });
    }
    
    let retrieveResult;
    try {
      retrieveResult = await retrieveData(testKey);
    } catch (retrieveError) {
      return NextResponse.json({
        success: false,
        ping: pingResult,
        storeResult,
        error: `Retrieve error: ${retrieveError instanceof Error ? retrieveError.message : 'Unknown retrieve error'}`,
        redisUrlSet: true,
        redisTokenSet: true
      });
    }
    
    return NextResponse.json({
      success: true,
      ping: pingResult,
      storeResult,
      retrieveResult,
      testKey,
      redisUrlSet: true,
      redisTokenSet: true
    });
  } catch (error) {
    console.error('Redis connection error:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
} 