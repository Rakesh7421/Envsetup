check status before act

# let 
##  publisher/main.py 
###     post things to platforms using publisher/poster.py 
####        FB+Insta
                First post content to facebook
                    Then get that fb post url to use that for posting into insta
####        Youtube 
                V2 Not implemented yet 
###     get content from `publisher/content_server.py` and 
            to avoid redundancy use publisher/data.csv
###     get Oauth info from Oauth/test_tokens_and_posting.py
            it will check tokens in oauth_tokens_*.json
                let oauth_tokens_*.json get page access tokens from  ./Oauth/*.py 
                    page access token is responsibility of ./Oauth/*.py 
            based on the output proceed, keep note u shall never trigger oauth because it may disrupt the existing tokens
###     Content_fetch
        
        Enhance the `publisher/fetch_content.py` module to fetch and validate content from the `/workspaces/Envsetup/publisher/fetch_contentt/*.py` feed, ensuring the feed contains at least one image or video. The implementation should:

        1. Parse and validate the feed structure, confirming it meets the minimum media requirement
        2. Extract all available images and videos with proper metadata (URLs, dimensions, formats)
        3. Implement robust error handling for malformed feeds or missing media
        4. Maintain backward compatibility with existing RSS functionality
        5. Include comprehensive logging for debugging and monitoring
        6. Support both synchronous and asynchronous fetching modes
        7. Validate media URLs and ensure they are accessible
        8. Generate a structured output containing:
           - Feed metadata (title, description, publication date)
           - Media inventory (counts, types, sizes)
           - Content validation status
           - Any encountered warnings or errors

        The solution should leverage the existing consolidated implementation while adding these validation capabilities without modifying the core fetching logic.


# skip stress on V2 just finish remaining