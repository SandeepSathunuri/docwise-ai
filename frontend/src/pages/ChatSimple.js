import React from 'react';
import { Container, Typography, Box } from '@mui/material';

const ChatSimple = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Chat with Your Documents
        </Typography>
        <Typography variant="body1">
          Chat functionality is being updated. Please check back soon!
        </Typography>
      </Box>
    </Container>
  );
};

export default ChatSimple;