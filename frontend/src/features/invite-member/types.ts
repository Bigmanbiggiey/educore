export interface InviteMemberInput {
  email: string;
  phone?: string;
  role_name: string;
}

export interface InviteMemberResult {
  user_id: string;
  email: string | null;
  role_name: string;
}
