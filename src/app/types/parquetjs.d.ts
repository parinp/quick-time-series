declare module 'parquetjs' {
  export class ParquetSchema {
    constructor(schema: Record<string, any>);
  }

  export class ParquetWriter {
    writer: {
      buffer: Buffer;
    };
    static openBuffer(schema: ParquetSchema): Promise<ParquetWriter>;
    appendRow(row: Record<string, any>): Promise<void>;
    close(): Promise<void>;
  }

  export class ParquetReader {
    static openBuffer(buffer: Buffer): Promise<ParquetReader>;
    getCursor(): ParquetCursor;
    close(): Promise<void>;
  }

  export class ParquetCursor {
    next(): Promise<Record<string, any> | null>;
  }
} 