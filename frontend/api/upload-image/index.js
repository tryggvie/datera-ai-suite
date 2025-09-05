import { put } from '@vercel/blob';

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Get the file from the request
    const file = req.body;
    
    if (!file) {
      return res.status(400).json({ error: 'No file provided' });
    }

    // Upload to Vercel Blob
    const blob = await put(req.headers['x-filename'] || 'image.jpg', file, {
      access: 'public',
      addRandomSuffix: true,
    });

    // Return the blob URL
    return res.status(200).json({
      url: blob.url,
      pathname: blob.pathname,
    });
  } catch (error) {
    console.error('Upload error:', error);
    return res.status(500).json({ 
      error: 'Upload failed', 
      details: error.message 
    });
  }
}

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '10mb',
    },
  },
};
