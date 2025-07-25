import React, { useState, useEffect } from 'react';
import {
    Container,
    Typography,
    Box,
    Grid,
    Card,
    CardContent,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    LinearProgress,
    Alert,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Button,
    Divider,
} from '@mui/material';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    LineChart,
    Line,
    PieChart,
    Pie,
    Cell,
    AreaChart,
    Area,
} from 'recharts';
import {
    Analytics as AnalyticsIcon,
    TrendingUp as TrendingUpIcon,
    QueryStats as QueryStatsIcon,
    Description as DocumentIcon,
    Chat as ChatIcon,
    Schedule as TimeIcon,
    Assessment as AssessmentIcon,
    Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useDocuments } from '../context/DocumentContext';
import { useChat } from '../context/ChatContext';
import { analyticsService } from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const MetricCard = ({ title, value, icon, color = 'primary', trend = null }) => (
    <Card sx={{ height: '100%' }}>
        <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                    sx={{
                        backgroundColor: `${color}.light`,
                        borderRadius: '50%',
                        p: 1,
                        mr: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    {icon}
                </Box>
                <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="div">
                        {title}
                    </Typography>
                    {trend && (
                        <Typography variant="caption" color={trend > 0 ? 'success.main' : 'error.main'}>
                            {trend > 0 ? '+' : ''}{trend}% from last period
                        </Typography>
                    )}
                </Box>
            </Box>
            <Typography variant="h4" component="div" color={`${color}.main`}>
                {value}
            </Typography>
        </CardContent>
    </Card>
);

const Analytics = () => {
    const { documents = [] } = useDocuments();
    const { getAllSessions = () => [], allMessages = [] } = useChat();
    const [analyticsData, setAnalyticsData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState('7d');
    const [error, setError] = useState(null);

    // Calculate local analytics from context data
    const calculateLocalAnalytics = () => {
        const sessions = getAllSessions ? getAllSessions() : [];
        const messages = allMessages || [];

        // Document analytics
        const totalDocuments = documents.length;
        const totalPages = documents.reduce((sum, doc) => sum + (doc.pages_count || 0), 0);
        const totalChunks = documents.reduce((sum, doc) => sum + (doc.chunks_count || 0), 0);
        const avgPagesPerDoc = totalDocuments > 0 ? (totalPages / totalDocuments).toFixed(1) : 0;

        // Chat analytics
        const totalSessions = sessions.length;
        const totalMessages = messages.length;
        const userMessages = messages.filter(msg => msg.isUser).length;
        const aiMessages = messages.filter(msg => !msg.isUser).length;
        const avgMessagesPerSession = totalSessions > 0 ? (totalMessages / totalSessions).toFixed(1) : 0;

        // Document usage analytics
        const documentUsage = documents.map(doc => {
            const docMessages = messages.filter(msg =>
                msg.sources && msg.sources.some(source => source.filename === doc.original_filename)
            );
            return {
                name: doc.original_filename.length > 20
                    ? doc.original_filename.substring(0, 20) + '...'
                    : doc.original_filename,
                fullName: doc.original_filename,
                queries: docMessages.length,
                pages: doc.pages_count || 0,
                chunks: doc.chunks_count || 0,
                uploadDate: doc.upload_date,
            };
        }).sort((a, b) => b.queries - a.queries);

        // Daily activity (last 7 days)
        const dailyActivity = [];
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];

            const dayMessages = messages.filter(msg => {
                const msgDate = new Date(msg.timestamp).toISOString().split('T')[0];
                return msgDate === dateStr;
            });

            dailyActivity.push({
                date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                messages: dayMessages.length,
                userMessages: dayMessages.filter(msg => msg.isUser).length,
                aiMessages: dayMessages.filter(msg => !msg.isUser).length,
            });
        }

        // Response confidence distribution
        const confidenceDistribution = [
            { range: '90-100%', count: 0, color: '#4CAF50' },
            { range: '70-89%', count: 0, color: '#8BC34A' },
            { range: '50-69%', count: 0, color: '#FFC107' },
            { range: '30-49%', count: 0, color: '#FF9800' },
            { range: '0-29%', count: 0, color: '#F44336' },
        ];

        messages.filter(msg => !msg.isUser && msg.confidence !== undefined).forEach(msg => {
            const confidence = msg.confidence * 100;
            if (confidence >= 90) confidenceDistribution[0].count++;
            else if (confidence >= 70) confidenceDistribution[1].count++;
            else if (confidence >= 50) confidenceDistribution[2].count++;
            else if (confidence >= 30) confidenceDistribution[3].count++;
            else confidenceDistribution[4].count++;
        });

        // Session length distribution
        const sessionLengths = sessions.map(session => ({
            sessionId: session.id,
            messageCount: session.messageCount,
            duration: 'N/A', // Would need session start/end times
        }));

        // Most active hours (if we had timestamp data)
        const hourlyActivity = Array.from({ length: 24 }, (_, hour) => ({
            hour: `${hour}:00`,
            messages: Math.floor(Math.random() * 10), // Placeholder data
        }));

        return {
            overview: {
                totalDocuments: totalDocuments || 0,
                totalPages: totalPages || 0,
                totalChunks: totalChunks || 0,
                avgPagesPerDoc: avgPagesPerDoc || 0,
                totalSessions: totalSessions || 0,
                totalMessages: totalMessages || 0,
                userMessages: userMessages || 0,
                aiMessages: aiMessages || 0,
                avgMessagesPerSession: avgMessagesPerSession || 0,
            },
            documentUsage: documentUsage || [],
            dailyActivity: dailyActivity || [],
            confidenceDistribution: confidenceDistribution || [],
            sessionLengths: sessionLengths || [],
            hourlyActivity: hourlyActivity || [],
        };
    };

    const fetchAnalytics = async () => {
        try {
            setLoading(true);
            setError(null);

            // Try to fetch from backend API
            try {
                const response = await analyticsService.getAnalytics(timeRange);
                setAnalyticsData(response.data);
            } catch (apiError) {
                // Fallback to local analytics if API is not available
                console.log('API not available, using local analytics');
                const localData = calculateLocalAnalytics();
                setAnalyticsData(localData);
            }
        } catch (err) {
            setError(err.message);
            // Still provide local analytics even if there's an error
            const localData = calculateLocalAnalytics();
            setAnalyticsData(localData);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, [timeRange, documents, allMessages]);

    const handleRefresh = () => {
        fetchAnalytics();
    };

    if (loading) {
        return (
            <Container maxWidth="lg">
                <Box sx={{ mt: 4 }}>
                    <LinearProgress />
                    <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
                        Loading analytics...
                    </Typography>
                </Box>
            </Container>
        );
    }

    if (!analyticsData) {
        return (
            <Container maxWidth="lg">
                <Alert severity="error" sx={{ mt: 4 }}>
                    Failed to load analytics data. Please try again.
                </Alert>
            </Container>
        );
    }

    // Provide default values to prevent undefined errors
    const {
        overview = {
            totalDocuments: 0,
            totalPages: 0,
            totalChunks: 0,
            avgPagesPerDoc: 0,
            totalSessions: 0,
            totalMessages: 0,
            userMessages: 0,
            aiMessages: 0,
            avgMessagesPerSession: 0,
        },
        documentUsage = [],
        dailyActivity = [],
        confidenceDistribution = [],
    } = analyticsData || {};

    return (
        <Container maxWidth="lg">
            {/* Header */}
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                    <Typography variant="h4" component="h1" gutterBottom>
                        Analytics Dashboard
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                        Insights into your RAG system usage and performance
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                        <InputLabel>Time Range</InputLabel>
                        <Select
                            value={timeRange}
                            label="Time Range"
                            onChange={(e) => setTimeRange(e.target.value)}
                        >
                            <MenuItem value="1d">Last 24 hours</MenuItem>
                            <MenuItem value="7d">Last 7 days</MenuItem>
                            <MenuItem value="30d">Last 30 days</MenuItem>
                            <MenuItem value="90d">Last 90 days</MenuItem>
                        </Select>
                    </FormControl>
                    <Button
                        variant="outlined"
                        startIcon={<RefreshIcon />}
                        onClick={handleRefresh}
                    >
                        Refresh
                    </Button>
                </Box>
            </Box>

            {error && (
                <Alert severity="warning" sx={{ mb: 3 }}>
                    API unavailable. Showing local analytics data.
                </Alert>
            )}

            {/* Overview Metrics */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <MetricCard
                        title="Total Documents"
                        value={overview.totalDocuments}
                        icon={<DocumentIcon />}
                        color="primary"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <MetricCard
                        title="Chat Sessions"
                        value={overview.totalSessions}
                        icon={<ChatIcon />}
                        color="secondary"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <MetricCard
                        title="Total Messages"
                        value={overview.totalMessages}
                        icon={<QueryStatsIcon />}
                        color="success"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <MetricCard
                        title="Avg Pages/Doc"
                        value={overview.avgPagesPerDoc}
                        icon={<AssessmentIcon />}
                        color="warning"
                    />
                </Grid>
            </Grid>

            {/* Charts Row 1 */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                {/* Daily Activity */}
                <Grid item xs={12} md={8}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Daily Activity
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <AreaChart data={dailyActivity}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="date" />
                                    <YAxis />
                                    <Tooltip />
                                    <Legend />
                                    <Area
                                        type="monotone"
                                        dataKey="messages"
                                        stackId="1"
                                        stroke="#8884d8"
                                        fill="#8884d8"
                                        name="Total Messages"
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="userMessages"
                                        stackId="2"
                                        stroke="#82ca9d"
                                        fill="#82ca9d"
                                        name="User Messages"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Response Confidence */}
                <Grid item xs={12} md={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Response Confidence
                            </Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie
                                        data={confidenceDistribution}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={({ range, count }) => count > 0 ? `${range}: ${count}` : ''}
                                        outerRadius={80}
                                        fill="#8884d8"
                                        dataKey="count"
                                    >
                                        {confidenceDistribution.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Document Usage Chart */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Document Usage Analytics
                            </Typography>
                            <ResponsiveContainer width="100%" height={400}>
                                <BarChart data={documentUsage}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="name" />
                                    <YAxis />
                                    <Tooltip
                                        formatter={(value, name) => [value, name]}
                                        labelFormatter={(label) => {
                                            const doc = documentUsage.find(d => d.name === label);
                                            return doc ? doc.fullName : label;
                                        }}
                                    />
                                    <Legend />
                                    <Bar dataKey="queries" fill="#8884d8" name="Queries" />
                                    <Bar dataKey="pages" fill="#82ca9d" name="Pages" />
                                    <Bar dataKey="chunks" fill="#ffc658" name="Chunks" />
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Document Usage Table */}
            <Grid container spacing={3}>
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" gutterBottom>
                                Document Performance Details
                            </Typography>
                            <TableContainer component={Paper} variant="outlined">
                                <Table>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Document Name</TableCell>
                                            <TableCell align="right">Queries</TableCell>
                                            <TableCell align="right">Pages</TableCell>
                                            <TableCell align="right">Chunks</TableCell>
                                            <TableCell align="right">Upload Date</TableCell>
                                            <TableCell align="right">Usage Rate</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {documentUsage.map((doc, index) => {
                                            const maxQueries = Math.max(...documentUsage.map(d => d.queries));
                                            const usageRate = maxQueries > 0 ? ((doc.queries / maxQueries) * 100).toFixed(1) : 0;

                                            return (
                                                <TableRow key={index}>
                                                    <TableCell component="th" scope="row">
                                                        <Typography variant="body2" noWrap>
                                                            {doc.fullName}
                                                        </Typography>
                                                    </TableCell>
                                                    <TableCell align="right">
                                                        <Chip
                                                            label={doc.queries}
                                                            size="small"
                                                            color={doc.queries > 0 ? 'primary' : 'default'}
                                                        />
                                                    </TableCell>
                                                    <TableCell align="right">{doc.pages}</TableCell>
                                                    <TableCell align="right">{doc.chunks}</TableCell>
                                                    <TableCell align="right">
                                                        {new Date(doc.uploadDate).toLocaleDateString()}
                                                    </TableCell>
                                                    <TableCell align="right">
                                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                            <LinearProgress
                                                                variant="determinate"
                                                                value={parseFloat(usageRate)}
                                                                sx={{ width: 60, height: 6 }}
                                                            />
                                                            <Typography variant="caption">
                                                                {usageRate}%
                                                            </Typography>
                                                        </Box>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Container>
    );
};

export default Analytics;