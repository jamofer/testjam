import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { bugsApi } from "../api/bugs"

export function useBugs(projectId, params = {}) {
  return useQuery({
    queryKey: ["bugs", projectId, params],
    queryFn: () => bugsApi.list(projectId, params),
    enabled: !!projectId,
  })
}

export function useBug(id) {
  return useQuery({
    queryKey: ["bug", id],
    queryFn: () => bugsApi.get(id),
    enabled: !!id,
  })
}

export function useBugComments(id) {
  return useQuery({
    queryKey: ["bug-comments", id],
    queryFn: () => bugsApi.listComments(id),
    enabled: !!id,
  })
}

export function useBugActivity(id) {
  return useQuery({
    queryKey: ["bug-activity", id],
    queryFn: () => bugsApi.listActivity(id),
    enabled: !!id,
  })
}

export function useCreateBug(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => bugsApi.create(projectId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bugs", projectId] }),
  })
}

export function useUpdateBug(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => bugsApi.update(id, data),
    onSuccess: (updated) => {
      queryClient.setQueryData(["bug", updated.id], updated)
      queryClient.invalidateQueries({ queryKey: ["bugs", projectId] })
    },
  })
}

export function useDeleteBug(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => bugsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bugs", projectId] }),
  })
}

export function useChangeBugStatus(projectId) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status, note }) => bugsApi.changeStatus(id, status, note),
    onSuccess: (updated) => {
      queryClient.setQueryData(["bug", updated.id], updated)
      queryClient.invalidateQueries({ queryKey: ["bugs", projectId] })
      queryClient.invalidateQueries({ queryKey: ["bug-activity", updated.id] })
    },
  })
}

export function useAddBugComment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }) => bugsApi.addComment(id, body),
    onSuccess: (comment) =>
      queryClient.invalidateQueries({ queryKey: ["bug-comments", comment.bug_id] }),
  })
}

export function useUpdateBugComment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ bugId, commentId, body }) =>
      bugsApi.updateComment(bugId, commentId, body),
    onSuccess: (comment) =>
      queryClient.invalidateQueries({ queryKey: ["bug-comments", comment.bug_id] }),
  })
}

export function useDeleteBugComment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ bugId, commentId }) => bugsApi.deleteComment(bugId, commentId),
    onSuccess: (_response, variables) =>
      queryClient.invalidateQueries({ queryKey: ["bug-comments", variables.bugId] }),
  })
}

export function useBugAttachments(id) {
  return useQuery({
    queryKey: ["bug-attachments", id],
    queryFn: () => bugsApi.listAttachments(id),
    enabled: !!id,
  })
}

export function useUploadBugAttachment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, file }) => bugsApi.uploadAttachment(id, file),
    onSuccess: (attachment) => {
      queryClient.invalidateQueries({ queryKey: ["bug-attachments", attachment.bug_id] })
      queryClient.invalidateQueries({ queryKey: ["bug-activity", attachment.bug_id] })
    },
  })
}

export function useDeleteBugAttachment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ bugId, attachmentId }) => bugsApi.deleteAttachment(bugId, attachmentId),
    onSuccess: (_response, variables) => {
      queryClient.invalidateQueries({ queryKey: ["bug-attachments", variables.bugId] })
      queryClient.invalidateQueries({ queryKey: ["bug-activity", variables.bugId] })
    },
  })
}

export function useBugContext(id) {
  return useQuery({
    queryKey: ["bug-context", id],
    queryFn: () => bugsApi.getContext(id),
    enabled: !!id,
  })
}

export function useBugLinks(id) {
  return useQuery({
    queryKey: ["bug-links", id],
    queryFn: () => bugsApi.listLinks(id),
    enabled: !!id,
  })
}

export function useAddBugLink() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => bugsApi.addLink(id, data),
    onSuccess: (link) =>
      queryClient.invalidateQueries({ queryKey: ["bug-links", link.bug_id] }),
  })
}

export function useDeleteBugLink() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ bugId, linkId }) => bugsApi.deleteLink(bugId, linkId),
    onSuccess: (_response, variables) =>
      queryClient.invalidateQueries({ queryKey: ["bug-links", variables.bugId] }),
  })
}

export function useBugWatchers(id) {
  return useQuery({
    queryKey: ["bug-watchers", id],
    queryFn: () => bugsApi.listWatchers(id),
    enabled: !!id,
  })
}

export function useWatchBug() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => bugsApi.watch(id),
    onSuccess: (bug) => {
      queryClient.setQueryData(["bug", bug.id], bug)
      queryClient.invalidateQueries({ queryKey: ["bug-watchers", bug.id] })
    },
  })
}

export function useUnwatchBug() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => bugsApi.unwatch(id),
    onSuccess: (bug) => {
      queryClient.setQueryData(["bug", bug.id], bug)
      queryClient.invalidateQueries({ queryKey: ["bug-watchers", bug.id] })
    },
  })
}
