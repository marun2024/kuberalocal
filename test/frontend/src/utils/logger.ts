type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  level: LogLevel;
  enabled: boolean;
  prefix?: string;
}

interface StructuredLogData {
  [key: string]: unknown;
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

class Logger {
  private config: LoggerConfig;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      level: config.level || (import.meta.env.DEV ? 'debug' : 'info'),
      enabled: config.enabled !== undefined ? config.enabled : true,
      prefix: config.prefix || '[KUBERA]',
    };
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled) return false;
    return LOG_LEVELS[level] >= LOG_LEVELS[this.config.level];
  }

  private formatMessage(message: string, data?: StructuredLogData): [string, ...unknown[]] {
    const timestamp = new Date().toISOString();
    const formattedMessage = `${this.config.prefix} ${timestamp} ${message}`;
    
    if (data && Object.keys(data).length > 0) {
      return [formattedMessage, data];
    }
    return [formattedMessage];
  }

  debug(message: string, data?: StructuredLogData): void {
    if (this.shouldLog('debug')) {
      console.log(...this.formatMessage(message, data));
    }
  }

  info(message: string, data?: StructuredLogData): void {
    if (this.shouldLog('info')) {
      console.info(...this.formatMessage(message, data));
    }
  }

  warn(message: string, data?: StructuredLogData): void {
    if (this.shouldLog('warn')) {
      console.warn(...this.formatMessage(message, data));
    }
  }

  error(message: string, data?: StructuredLogData): void {
    if (this.shouldLog('error')) {
      console.error(...this.formatMessage(message, data));
    }
  }

  // Console features for better debugging
  group(label: string): void {
    if (this.config.enabled) {
      console.group(`${this.config.prefix} ${label}`);
    }
  }

  groupCollapsed(label: string): void {
    if (this.config.enabled) {
      console.groupCollapsed(`${this.config.prefix} ${label}`);
    }
  }

  groupEnd(): void {
    if (this.config.enabled) {
      console.groupEnd();
    }
  }

  table(data: unknown): void {
    if (this.config.enabled && this.shouldLog('debug')) {
      console.table(data);
    }
  }

  time(label: string): void {
    if (this.config.enabled && this.shouldLog('debug')) {
      console.time(`${this.config.prefix} ${label}`);
    }
  }

  timeEnd(label: string): void {
    if (this.config.enabled && this.shouldLog('debug')) {
      console.timeEnd(`${this.config.prefix} ${label}`);
    }
  }

  trace(message: string, data?: StructuredLogData): void {
    if (this.shouldLog('debug')) {
      console.trace(...this.formatMessage(message, data));
    }
  }

  setLevel(level: LogLevel): void {
    this.config.level = level;
  }

  setPrefix(prefix: string): void {
    this.config.prefix = prefix;
  }

  disable(): void {
    this.config.enabled = false;
  }

  enable(): void {
    this.config.enabled = true;
  }
}

export const logger = new Logger();
export default logger;