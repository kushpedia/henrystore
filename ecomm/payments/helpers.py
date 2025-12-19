
def categorize_mpesa_error(result_code):
    """Categorize M-Pesa error for better handling"""
    user_errors = [1032, 2001]  # Cancelled by user, Invalid PIN
    balance_errors = [1]  # Insufficient balance
    limit_errors = [2, 3, 4, 5, 8, 17, 18]  # Various limit errors
    timeout_errors = [10, 1019, 1037]  # Timeout, expired, unreachable
    system_errors = [9, 11, 12, 13, 14, 15, 16, 20, 26, 29]  # System/validation errors
    
    if result_code in user_errors:
        return 'user_error'
    elif result_code in balance_errors:
        return 'balance_error'
    elif result_code in limit_errors:
        return 'limit_error'
    elif result_code in timeout_errors:
        return 'timeout_error'
    elif result_code in system_errors:
        return 'system_error'
    else:
        return 'unknown_error'

def should_auto_retry(result_code):
    """Determine if payment should be auto-retried"""
    auto_retry_codes = [1037, 1019, 10]  # Timeout, expired, unreachable
    
    if result_code in auto_retry_codes:
        return True
    return False

def get_retry_delay(result_code):
    """Get appropriate retry delay based on error"""
    if result_code == 1037:  # User unreachable
        return 30  # 30 seconds
    elif result_code == 1019:  # Transaction expired
        return 10  # 10 seconds
    elif result_code == 10:  # Timeout
        return 60  # 60 seconds
    return 5  # Default 5 seconds