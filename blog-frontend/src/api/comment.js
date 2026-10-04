import api from './index'

// 获取文章评论
export function getComments(articleId) {
  return api.get(`/comments/article/${articleId}/`)
}

// 创建评论
export function createComment(data) {
  return api.post('/comments/create/', data)
}

// 删除评论
export function deleteComment(id) {
  return api.delete(`/comments/${id}/delete/`)
}
