import request from './request'

// ===== 余量魔法袋（公开浏览）=====
export const getBags = (params) => request.get('/surplus-bags/', { params })
export const getBag = (id) => request.get(`/surplus-bags/${id}`)
export const createBag = (data) => request.post('/surplus-bags/', data)
export const updateBag = (id, data) => request.put(`/surplus-bags/${id}`, data)
export const deleteBag = (id) => request.delete(`/surplus-bags/${id}`)

// ===== 订单 =====
export const createOrder = (data) => request.post('/orders/', data)
export const getMyOrders = () => request.get('/orders/')
export const getOrder = (id) => request.get(`/orders/${id}`)
export const cancelOrder = (orderNo, phone) =>
  request.post(`/v1/orders/${orderNo}/cancel`, { customer_phone: phone })
export const verifyStoreOrder = (id) => request.put(`/orders/${id}/verify`)

// ===== 门店自提点 =====
export const getStores = () => request.get('/stores/')

// ===== 站内通知 =====
export const getNotifications = () => request.get('/notifications/')
export const getUnreadCount = () => request.get('/notifications/unread-count')
export const readAllNotifications = () => request.put('/notifications/read-all')

// ===== 图片上传 =====
export const uploadImage = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/upload/image', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ===== 碳减排统计 =====
export const getCarbonSummary = (userId) =>
  request.get('/carbon/user/summary', { params: { user_id: userId } })
export const getCarbonRecords = (userId, params) =>
  request.get('/carbon/user/records', { params: { user_id: userId, ...params } })
export const getPlatformCarbon = () => request.get('/carbon/platform/summary')
