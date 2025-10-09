# Automatic S3 Data Updates

The JLG Provider Recommender now automatically updates data from your configured S3 buckets when the app launches.

## How It Works

1. **On App Launch**: The app automatically checks if S3 is properly configured
2. **Data Download**: If configured, it downloads the latest files from both referrals and preferred providers folders
3. **Processing**: The downloaded files are automatically processed and saved to the local `data/processed/` directory
4. **Cache Refresh**: All data caches are refreshed to use the new data
5. **Notification**: Users see a brief success message on the Home and Search pages

## Configuration

The auto-update feature uses the same S3 configuration as the manual Update Data page:

- **AWS Access Key ID**: Required
- **AWS Secret Access Key**: Required
- **S3 Bucket Name**: Required
- **Referrals Folder**: Configurable (default: "990046944")
- **Preferred Providers Folder**: Configurable (default: "990047553")

## Behavior

### When S3 is Configured
- ✅ Automatically downloads and processes latest files
- ✅ Shows success notification to users
- ✅ Logs all activity for debugging

### When S3 is Not Configured
- ⚠️ Silently skips auto-update
- ⚠️ No error messages to users
- ⚠️ Falls back to existing local data files

### When S3 Has Issues
- ❌ Logs errors for administrators
- ❌ Gracefully continues with existing data
- ❌ Does not block app startup

## Performance

- **Runs Once**: Only executes once per browser session
- **Non-Blocking**: Does not prevent users from using the app
- **Parallel Processing**: Downloads referrals and providers files simultaneously
- **Smart Caching**: Uses optimized S3 client with connection pooling

## User Experience

Users will see:
1. A brief success message: "✅ Data automatically updated from S3: referrals (filename), providers (filename)"
2. The message appears on the Home page and Search page
3. The message automatically disappears after being shown once

## Troubleshooting

### No Auto-Update Occurring
1. Check S3 configuration in secrets
2. Verify bucket permissions
3. Check application logs for errors

### Partial Updates
- If only referrals OR providers update, that's normal
- The app will process whatever files are available
- Check S3 folders for file availability

### Performance Issues
- Auto-update uses optimized batch operations
- Connection pooling minimizes latency
- Files are processed in parallel when possible

## Technical Details

### Session State Management
- `s3_auto_update_completed`: Prevents multiple runs per session
- `s3_auto_update_success`: Stores success message for display

### Functions Added
- `auto_update_data_from_s3()`: Main auto-update logic in app.py
- `show_auto_update_status()`: Displays success messages on pages

### Error Handling
- All errors are logged but do not interrupt app startup
- Graceful fallbacks ensure app functionality is maintained
- Invalid configurations are detected and reported appropriately
