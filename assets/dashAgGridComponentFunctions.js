var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.ViewOnSeekButton = function (props) {
    const { setData, data } = props;
    
    function onClick() {
        const jobId = props.data['Job Id'];
        window.open('https://www.seek.com.au/job/' + jobId, '_blank');
        setData({ jobId: jobId, timestamp: new Date().getTime() });
    }
    
    return React.createElement(
        'button',
        {
            onClick: onClick,
            className: 'btn btn-primary btn-sm',
            style: { cursor: 'pointer' }
        },
        'View on Seek'
    );
};

dagcomponentfuncs.ViewDetailsButton = function (props) {
    const { setData, data } = props;
    
    function onClick() {
        setData({ 
            colId: 'details',
            data: props.data,
            timestamp: new Date().getTime() 
        });
    }
    
    return React.createElement(
        'button',
        {
            onClick: onClick,
            className: 'btn btn-info btn-sm',
            style: { cursor: 'pointer' }
        },
        'View Details'
    );
};

dagcomponentfuncs.ActionButtons = function (props) {
    const { setData, data } = props;
    
    function onViewDetailsClick() {
        setData({ 
            colId: 'details',
            data: props.data,
            timestamp: new Date().getTime() 
        });
    }
    
    function onViewOnSeekClick() {
        window.open(`https://www.seek.com.au/job/${props.data['Job Id']}`, '_blank');
    }
    
    return React.createElement(
        'div',
        {
            style: { 
                display: 'flex',
                gap: '8px',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
                width: '100%'
            }
        },
        [
            React.createElement(
                'button',
                {
                    onClick: onViewDetailsClick,
                    className: 'btn btn-info btn-sm',
                    style: { cursor: 'pointer' }
                },
                'View Details'
            ),
            React.createElement(
                'button',
                {
                    onClick: onViewOnSeekClick,
                    className: 'btn btn-primary btn-sm',
                    style: { cursor: 'pointer' }
                },
                'View on Seek'
            )
        ]
    );
};