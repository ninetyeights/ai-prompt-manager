from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from urllib.parse import urlparse, parse_qs


class CustomPageNumberPagination(PageNumberPagination):
    def get_page_number_from_url(self, url):
        """从URL中提取页码"""
        if url:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            return int(query_params.get('page', [None])[0]) if 'page' in query_params else None
        return None

    def get_paginated_response(self, data):
        count = self.page.paginator.count
        current_page = self.page.number
        total_pages = self.page.paginator.num_pages

        previous_page = self.get_page_number_from_url(self.get_previous_link())
        if previous_page is None and current_page > 1:
            previous_page = current_page - 1

        next_page = self.get_page_number_from_url(self.get_next_link())

        return Response({
            'count': count,
            'current_page': current_page,
            'total_pages': total_pages,
            'next_page': next_page,
            'previous_page': previous_page,
            'result_count': len(data),
            'results': data,
        })