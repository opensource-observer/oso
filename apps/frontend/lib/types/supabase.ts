export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
      admin_users: {
        Row: {
          created_at: string;
          description: string | null;
          id: number;
          name: string;
          updated_at: string;
          user_id: string;
        };
        Insert: {
          created_at?: string;
          description?: string | null;
          id?: number;
          name: string;
          updated_at?: string;
          user_id: string;
        };
        Update: {
          created_at?: string;
          description?: string | null;
          id?: number;
          name?: string;
          updated_at?: string;
          user_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "admin_users_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
        ];
      };
      api_keys: {
        Row: {
          api_key: string;
          created_at: string;
          deleted_at: string | null;
          id: string;
          name: string;
          org_id: string;
          updated_at: string;
          user_id: string;
        };
        Insert: {
          api_key: string;
          created_at?: string;
          deleted_at?: string | null;
          id?: string;
          name: string;
          org_id: string;
          updated_at?: string;
          user_id: string;
        };
        Update: {
          api_key?: string;
          created_at?: string;
          deleted_at?: string | null;
          id?: string;
          name?: string;
          org_id?: string;
          updated_at?: string;
          user_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "api_keys_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "api_keys_user_id_fkey1";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
        ];
      };
      chat_history: {
        Row: {
          created_at: string;
          created_by: string;
          data: string | null;
          deleted_at: string | null;
          display_name: string;
          id: string;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          created_by: string;
          data?: string | null;
          deleted_at?: string | null;
          display_name: string;
          id?: string;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          created_by?: string;
          data?: string | null;
          deleted_at?: string | null;
          display_name?: string;
          id?: string;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "chat_history_created_by_fkey";
            columns: ["created_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "chat_history_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      connector_relationships: {
        Row: {
          id: string;
          org_id: string;
          source_column_name: string;
          source_table_id: string;
          target_column_name: string | null;
          target_oso_entity: string | null;
          target_table_id: string | null;
        };
        Insert: {
          id?: string;
          org_id: string;
          source_column_name: string;
          source_table_id: string;
          target_column_name?: string | null;
          target_oso_entity?: string | null;
          target_table_id?: string | null;
        };
        Update: {
          id?: string;
          org_id?: string;
          source_column_name?: string;
          source_table_id?: string;
          target_column_name?: string | null;
          target_oso_entity?: string | null;
          target_table_id?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "fk_org_id";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "fk_source_column";
            columns: ["source_table_id", "source_column_name"];
            isOneToOne: false;
            referencedRelation: "dynamic_column_contexts";
            referencedColumns: ["table_id", "column_name"];
          },
          {
            foreignKeyName: "fk_source_table";
            columns: ["source_table_id"];
            isOneToOne: false;
            referencedRelation: "dynamic_table_contexts";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "fk_target_column";
            columns: ["target_table_id", "target_column_name"];
            isOneToOne: false;
            referencedRelation: "dynamic_column_contexts";
            referencedColumns: ["table_id", "column_name"];
          },
          {
            foreignKeyName: "fk_target_table";
            columns: ["target_table_id"];
            isOneToOne: false;
            referencedRelation: "dynamic_table_contexts";
            referencedColumns: ["id"];
          },
        ];
      };
      data_ingestions: {
        Row: {
          config: Json;
          created_at: string;
          dataset_id: string;
          deleted_at: string | null;
          factory_type: string;
          id: string;
          name: string;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          config: Json;
          created_at?: string;
          dataset_id: string;
          deleted_at?: string | null;
          factory_type: string;
          id?: string;
          name: string;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          config?: Json;
          created_at?: string;
          dataset_id?: string;
          deleted_at?: string | null;
          factory_type?: string;
          id?: string;
          name?: string;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "data_ingestions_dataset_id_fkey";
            columns: ["dataset_id"];
            isOneToOne: false;
            referencedRelation: "datasets";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "fk_data_ingestions_org_id";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      datasets: {
        Row: {
          created_at: string;
          created_by: string;
          dataset_type: Database["public"]["Enums"]["dataset_type"];
          deleted_at: string | null;
          description: string | null;
          display_name: string;
          id: string;
          is_public: boolean;
          name: string;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          created_by: string;
          dataset_type: Database["public"]["Enums"]["dataset_type"];
          deleted_at?: string | null;
          description?: string | null;
          display_name: string;
          id?: string;
          is_public?: boolean;
          name: string;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          created_by?: string;
          dataset_type?: Database["public"]["Enums"]["dataset_type"];
          deleted_at?: string | null;
          description?: string | null;
          display_name?: string;
          id?: string;
          is_public?: boolean;
          name?: string;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "datasets_created_by_fkey";
            columns: ["created_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "datasets_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      datasets_by_organization: {
        Row: {
          created_at: string;
          dataset_id: string;
          deleted_at: string | null;
          id: string;
          org_id: string;
        };
        Insert: {
          created_at?: string;
          dataset_id: string;
          deleted_at?: string | null;
          id?: string;
          org_id: string;
        };
        Update: {
          created_at?: string;
          dataset_id?: string;
          deleted_at?: string | null;
          id?: string;
          org_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "datasets_by_organization_dataset_id_fkey";
            columns: ["dataset_id"];
            isOneToOne: false;
            referencedRelation: "datasets";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "datasets_by_organization_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      dynamic_column_contexts: {
        Row: {
          column_name: string;
          data_type: string;
          description: string | null;
          sample_data: string | null;
          table_id: string;
        };
        Insert: {
          column_name: string;
          data_type: string;
          description?: string | null;
          sample_data?: string | null;
          table_id: string;
        };
        Update: {
          column_name?: string;
          data_type?: string;
          description?: string | null;
          sample_data?: string | null;
          table_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "fk_table_context";
            columns: ["table_id"];
            isOneToOne: false;
            referencedRelation: "dynamic_table_contexts";
            referencedColumns: ["id"];
          },
        ];
      };
      dynamic_connectors: {
        Row: {
          config: Json | null;
          connector_name: string;
          connector_type: string;
          created_at: string;
          created_by: string;
          deleted_at: string | null;
          id: string;
          is_public: boolean | null;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          config?: Json | null;
          connector_name: string;
          connector_type: string;
          created_at?: string;
          created_by: string;
          deleted_at?: string | null;
          id?: string;
          is_public?: boolean | null;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          config?: Json | null;
          connector_name?: string;
          connector_type?: string;
          created_at?: string;
          created_by?: string;
          deleted_at?: string | null;
          id?: string;
          is_public?: boolean | null;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "fk_org_id";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      dynamic_replications: {
        Row: {
          config: Json;
          created_at: string;
          created_by: string;
          credentials_path: string | null;
          deleted_at: string | null;
          id: string;
          org_id: string;
          replication_name: string;
          replication_type: string;
          updated_at: string;
        };
        Insert: {
          config: Json;
          created_at?: string;
          created_by: string;
          credentials_path?: string | null;
          deleted_at?: string | null;
          id?: string;
          org_id: string;
          replication_name: string;
          replication_type: string;
          updated_at?: string;
        };
        Update: {
          config?: Json;
          created_at?: string;
          created_by?: string;
          credentials_path?: string | null;
          deleted_at?: string | null;
          id?: string;
          org_id?: string;
          replication_name?: string;
          replication_type?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "fk_org_id";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      dynamic_table_contexts: {
        Row: {
          connector_id: string;
          description: string | null;
          id: string;
          table_name: string;
        };
        Insert: {
          connector_id: string;
          description?: string | null;
          id?: string;
          table_name: string;
        };
        Update: {
          connector_id?: string;
          description?: string | null;
          id?: string;
          table_name?: string;
        };
        Relationships: [
          {
            foreignKeyName: "fk_connector_id";
            columns: ["connector_id"];
            isOneToOne: false;
            referencedRelation: "dynamic_connectors";
            referencedColumns: ["id"];
          },
        ];
      };
      invitations: {
        Row: {
          accepted_at: string | null;
          accepted_by: string | null;
          created_at: string;
          deleted_at: string | null;
          email: string;
          expires_at: string;
          id: string;
          invited_by: string;
          org_id: string;
          org_name: string;
          updated_at: string;
        };
        Insert: {
          accepted_at?: string | null;
          accepted_by?: string | null;
          created_at?: string;
          deleted_at?: string | null;
          email: string;
          expires_at?: string;
          id?: string;
          invited_by: string;
          org_id: string;
          org_name: string;
          updated_at?: string;
        };
        Update: {
          accepted_at?: string | null;
          accepted_by?: string | null;
          created_at?: string;
          deleted_at?: string | null;
          email?: string;
          expires_at?: string;
          id?: string;
          invited_by?: string;
          org_id?: string;
          org_name?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "invitations_accepted_by_fkey";
            columns: ["accepted_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "invitations_invited_by_fkey";
            columns: ["invited_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "invitations_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      materialization: {
        Row: {
          created_at: string;
          dataset_id: string;
          id: string;
          org_id: string;
          run_id: string;
          schema: Database["public"]["CompositeTypes"]["model_column_type"][];
          step_id: string | null;
          table_id: string;
          warehouse_fqn: string;
        };
        Insert: {
          created_at?: string;
          dataset_id: string;
          id?: string;
          org_id: string;
          run_id: string;
          schema: Database["public"]["CompositeTypes"]["model_column_type"][];
          step_id?: string | null;
          table_id: string;
          warehouse_fqn: string;
        };
        Update: {
          created_at?: string;
          dataset_id?: string;
          id?: string;
          org_id?: string;
          run_id?: string;
          schema?: Database["public"]["CompositeTypes"]["model_column_type"][];
          step_id?: string | null;
          table_id?: string;
          warehouse_fqn?: string;
        };
        Relationships: [
          {
            foreignKeyName: "fk_step";
            columns: ["step_id"];
            isOneToOne: false;
            referencedRelation: "step";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "materialization_dataset_id_fkey";
            columns: ["dataset_id"];
            isOneToOne: false;
            referencedRelation: "datasets";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "materialization_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "materialization_run_id_fkey";
            columns: ["run_id"];
            isOneToOne: false;
            referencedRelation: "run";
            referencedColumns: ["id"];
          },
        ];
      };
      model: {
        Row: {
          created_at: string;
          dataset_id: string;
          deleted_at: string | null;
          id: string;
          is_enabled: boolean;
          name: string;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          dataset_id: string;
          deleted_at?: string | null;
          id?: string;
          is_enabled?: boolean;
          name: string;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          dataset_id?: string;
          deleted_at?: string | null;
          id?: string;
          is_enabled?: boolean;
          name?: string;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "model_dataset_id_fkey";
            columns: ["dataset_id"];
            isOneToOne: false;
            referencedRelation: "datasets";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "model_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      model_release: {
        Row: {
          created_at: string;
          description: string | null;
          id: string;
          model_id: string;
          model_revision_id: string;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          description?: string | null;
          id?: string;
          model_id: string;
          model_revision_id: string;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          description?: string | null;
          id?: string;
          model_id?: string;
          model_revision_id?: string;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "model_release_model_id_fkey";
            columns: ["model_id"];
            isOneToOne: false;
            referencedRelation: "model";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "model_release_model_revision_id_fkey";
            columns: ["model_revision_id"];
            isOneToOne: false;
            referencedRelation: "model_revision";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "model_release_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      model_revision: {
        Row: {
          clustered_by: string[] | null;
          code: string;
          created_at: string;
          cron: string;
          depends_on:
            | Database["public"]["CompositeTypes"]["model_dependency_type"][]
            | null;
          description: string | null;
          end: string | null;
          hash: string;
          id: string;
          kind: Database["public"]["Enums"]["model_kind"];
          kind_options:
            | Database["public"]["CompositeTypes"]["model_kind_options"]
            | null;
          language: string;
          model_id: string;
          name: string;
          org_id: string;
          partitioned_by: string[] | null;
          revision_number: number;
          schema: Database["public"]["CompositeTypes"]["model_column_type"][];
          start: string | null;
        };
        Insert: {
          clustered_by?: string[] | null;
          code: string;
          created_at?: string;
          cron: string;
          depends_on?:
            | Database["public"]["CompositeTypes"]["model_dependency_type"][]
            | null;
          description?: string | null;
          end?: string | null;
          hash: string;
          id?: string;
          kind: Database["public"]["Enums"]["model_kind"];
          kind_options?:
            | Database["public"]["CompositeTypes"]["model_kind_options"]
            | null;
          language: string;
          model_id: string;
          name: string;
          org_id: string;
          partitioned_by?: string[] | null;
          revision_number: number;
          schema: Database["public"]["CompositeTypes"]["model_column_type"][];
          start?: string | null;
        };
        Update: {
          clustered_by?: string[] | null;
          code?: string;
          created_at?: string;
          cron?: string;
          depends_on?:
            | Database["public"]["CompositeTypes"]["model_dependency_type"][]
            | null;
          description?: string | null;
          end?: string | null;
          hash?: string;
          id?: string;
          kind?: Database["public"]["Enums"]["model_kind"];
          kind_options?:
            | Database["public"]["CompositeTypes"]["model_kind_options"]
            | null;
          language?: string;
          model_id?: string;
          name?: string;
          org_id?: string;
          partitioned_by?: string[] | null;
          revision_number?: number;
          schema?: Database["public"]["CompositeTypes"]["model_column_type"][];
          start?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "model_revision_model_id_fkey";
            columns: ["model_id"];
            isOneToOne: false;
            referencedRelation: "model";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "model_revision_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      notebooks: {
        Row: {
          created_at: string;
          created_by: string;
          data: string | null;
          deleted_at: string | null;
          description: string | null;
          id: string;
          notebook_name: string;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          created_by: string;
          data?: string | null;
          deleted_at?: string | null;
          description?: string | null;
          id?: string;
          notebook_name: string;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          created_by?: string;
          data?: string | null;
          deleted_at?: string | null;
          description?: string | null;
          id?: string;
          notebook_name?: string;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "saved_queries_created_by_fkey";
            columns: ["created_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "saved_queries_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      organization_credit_transactions: {
        Row: {
          amount: number;
          api_endpoint: string | null;
          created_at: string;
          id: string;
          metadata: Json | null;
          org_id: string;
          transaction_type: string;
          user_id: string;
        };
        Insert: {
          amount: number;
          api_endpoint?: string | null;
          created_at?: string;
          id?: string;
          metadata?: Json | null;
          org_id: string;
          transaction_type: string;
          user_id: string;
        };
        Update: {
          amount?: number;
          api_endpoint?: string | null;
          created_at?: string;
          id?: string;
          metadata?: Json | null;
          org_id?: string;
          transaction_type?: string;
          user_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "organization_credit_transactions_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      organization_credits: {
        Row: {
          created_at: string;
          credits_balance: number;
          id: string;
          last_refill_at: string | null;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          credits_balance?: number;
          id?: string;
          last_refill_at?: string | null;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          credits_balance?: number;
          id?: string;
          last_refill_at?: string | null;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "organization_credits_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: true;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      organizations: {
        Row: {
          billing_contact_email: string | null;
          created_at: string;
          created_by: string;
          deleted_at: string | null;
          enterprise_support_url: string | null;
          id: string;
          org_name: string;
          plan_id: string;
          updated_at: string;
        };
        Insert: {
          billing_contact_email?: string | null;
          created_at?: string;
          created_by: string;
          deleted_at?: string | null;
          enterprise_support_url?: string | null;
          id?: string;
          org_name: string;
          plan_id?: string;
          updated_at?: string;
        };
        Update: {
          billing_contact_email?: string | null;
          created_at?: string;
          created_by?: string;
          deleted_at?: string | null;
          enterprise_support_url?: string | null;
          id?: string;
          org_name?: string;
          plan_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "organizations_created_by_fkey1";
            columns: ["created_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "organizations_plan_id_fkey";
            columns: ["plan_id"];
            isOneToOne: false;
            referencedRelation: "pricing_plan";
            referencedColumns: ["plan_id"];
          },
        ];
      };
      pricing_plan: {
        Row: {
          created_at: string;
          max_credits_per_cycle: number | null;
          plan_id: string;
          plan_name: string;
          price_per_credit: number;
          priority: number;
          refill_cycle_days: number | null;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          max_credits_per_cycle?: number | null;
          plan_id?: string;
          plan_name: string;
          price_per_credit: number;
          priority?: number;
          refill_cycle_days?: number | null;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          max_credits_per_cycle?: number | null;
          plan_id?: string;
          plan_name?: string;
          price_per_credit?: number;
          priority?: number;
          refill_cycle_days?: number | null;
          updated_at?: string;
        };
        Relationships: [];
      };
      published_notebooks: {
        Row: {
          created_at: string;
          data_path: string;
          deleted_at: string | null;
          id: string;
          notebook_id: string;
          updated_at: string;
          updated_by: string | null;
        };
        Insert: {
          created_at?: string;
          data_path: string;
          deleted_at?: string | null;
          id?: string;
          notebook_id: string;
          updated_at?: string;
          updated_by?: string | null;
        };
        Update: {
          created_at?: string;
          data_path?: string;
          deleted_at?: string | null;
          id?: string;
          notebook_id?: string;
          updated_at?: string;
          updated_by?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "published_notebooks_notebook_id_fkey";
            columns: ["notebook_id"];
            isOneToOne: false;
            referencedRelation: "notebooks";
            referencedColumns: ["id"];
          },
        ];
      };
      purchase_intents: {
        Row: {
          completed_at: string | null;
          created_at: string;
          credits_amount: number;
          id: string;
          metadata: Json | null;
          org_id: string | null;
          package_id: string;
          price_cents: number;
          status: string;
          stripe_session_id: string;
          user_id: string;
        };
        Insert: {
          completed_at?: string | null;
          created_at?: string;
          credits_amount: number;
          id?: string;
          metadata?: Json | null;
          org_id?: string | null;
          package_id: string;
          price_cents: number;
          status?: string;
          stripe_session_id: string;
          user_id: string;
        };
        Update: {
          completed_at?: string | null;
          created_at?: string;
          credits_amount?: number;
          id?: string;
          metadata?: Json | null;
          org_id?: string | null;
          package_id?: string;
          price_cents?: number;
          status?: string;
          stripe_session_id?: string;
          user_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: "purchase_intents_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      reserved_names: {
        Row: {
          created_at: string;
          name: string;
        };
        Insert: {
          created_at?: string;
          name: string;
        };
        Update: {
          created_at?: string;
          name?: string;
        };
        Relationships: [];
      };
      resource_permissions: {
        Row: {
          chat_id: string | null;
          created_at: string;
          granted_by: string | null;
          id: string;
          notebook_id: string | null;
          permission_level: string;
          revoked_at: string | null;
          updated_at: string;
          user_id: string | null;
        };
        Insert: {
          chat_id?: string | null;
          created_at?: string;
          granted_by?: string | null;
          id?: string;
          notebook_id?: string | null;
          permission_level: string;
          revoked_at?: string | null;
          updated_at?: string;
          user_id?: string | null;
        };
        Update: {
          chat_id?: string | null;
          created_at?: string;
          granted_by?: string | null;
          id?: string;
          notebook_id?: string | null;
          permission_level?: string;
          revoked_at?: string | null;
          updated_at?: string;
          user_id?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "resource_permissions_chat_id_fkey";
            columns: ["chat_id"];
            isOneToOne: false;
            referencedRelation: "chat_history";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "resource_permissions_granted_by_fkey";
            columns: ["granted_by"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "resource_permissions_notebook_id_fkey";
            columns: ["notebook_id"];
            isOneToOne: false;
            referencedRelation: "notebooks";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "resource_permissions_user_id_fkey";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
        ];
      };
      run: {
        Row: {
          completed_at: string | null;
          dataset_id: string | null;
          id: string;
          logs_url: string | null;
          metadata: Json | null;
          models: string[] | null;
          org_id: string;
          queued_at: string;
          requested_by: string | null;
          run_type: Database["public"]["Enums"]["run_type"];
          started_at: string | null;
          status: Database["public"]["Enums"]["run_status"];
          status_code: number | null;
          ttl: string | null;
        };
        Insert: {
          completed_at?: string | null;
          dataset_id?: string | null;
          id?: string;
          logs_url?: string | null;
          metadata?: Json | null;
          models?: string[] | null;
          org_id: string;
          queued_at?: string;
          requested_by?: string | null;
          run_type?: Database["public"]["Enums"]["run_type"];
          started_at?: string | null;
          status?: Database["public"]["Enums"]["run_status"];
          status_code?: number | null;
          ttl?: string | null;
        };
        Update: {
          completed_at?: string | null;
          dataset_id?: string | null;
          id?: string;
          logs_url?: string | null;
          metadata?: Json | null;
          models?: string[] | null;
          org_id?: string;
          queued_at?: string;
          requested_by?: string | null;
          run_type?: Database["public"]["Enums"]["run_type"];
          started_at?: string | null;
          status?: Database["public"]["Enums"]["run_status"];
          status_code?: number | null;
          ttl?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "run_dataset_id_fkey";
            columns: ["dataset_id"];
            isOneToOne: false;
            referencedRelation: "datasets";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "run_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      static_model: {
        Row: {
          created_at: string;
          dataset_id: string;
          deleted_at: string | null;
          id: string;
          name: string;
          org_id: string;
          updated_at: string;
        };
        Insert: {
          created_at?: string;
          dataset_id: string;
          deleted_at?: string | null;
          id?: string;
          name: string;
          org_id: string;
          updated_at?: string;
        };
        Update: {
          created_at?: string;
          dataset_id?: string;
          deleted_at?: string | null;
          id?: string;
          name?: string;
          org_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "static_model_dataset_id_fkey";
            columns: ["dataset_id"];
            isOneToOne: false;
            referencedRelation: "datasets";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "static_model_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      step: {
        Row: {
          completed_at: string | null;
          display_name: string;
          id: string;
          logs_url: string | null;
          name: string;
          org_id: string;
          run_id: string;
          started_at: string;
          status: Database["public"]["Enums"]["step_status"];
        };
        Insert: {
          completed_at?: string | null;
          display_name: string;
          id?: string;
          logs_url?: string | null;
          name: string;
          org_id: string;
          run_id: string;
          started_at?: string;
          status?: Database["public"]["Enums"]["step_status"];
        };
        Update: {
          completed_at?: string | null;
          display_name?: string;
          id?: string;
          logs_url?: string | null;
          name?: string;
          org_id?: string;
          run_id?: string;
          started_at?: string;
          status?: Database["public"]["Enums"]["step_status"];
        };
        Relationships: [
          {
            foreignKeyName: "step_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "step_run_id_fkey";
            columns: ["run_id"];
            isOneToOne: false;
            referencedRelation: "run";
            referencedColumns: ["id"];
          },
        ];
      };
      user_credits: {
        Row: {
          created_at: string;
          credits_balance: number;
          id: string;
          updated_at: string;
          user_id: string;
        };
        Insert: {
          created_at?: string;
          credits_balance?: number;
          id?: string;
          updated_at?: string;
          user_id: string;
        };
        Update: {
          created_at?: string;
          credits_balance?: number;
          id?: string;
          updated_at?: string;
          user_id?: string;
        };
        Relationships: [];
      };
      user_profiles: {
        Row: {
          avatar_url: string | null;
          email: string | null;
          full_name: string | null;
          id: string;
          updated_at: string | null;
          website: string | null;
        };
        Insert: {
          avatar_url?: string | null;
          email?: string | null;
          full_name?: string | null;
          id: string;
          updated_at?: string | null;
          website?: string | null;
        };
        Update: {
          avatar_url?: string | null;
          email?: string | null;
          full_name?: string | null;
          id?: string;
          updated_at?: string | null;
          website?: string | null;
        };
        Relationships: [];
      };
      users_by_organization: {
        Row: {
          created_at: string;
          deleted_at: string | null;
          id: string;
          org_id: string;
          updated_at: string;
          user_id: string;
          user_role: string;
        };
        Insert: {
          created_at?: string;
          deleted_at?: string | null;
          id?: string;
          org_id: string;
          updated_at?: string;
          user_id: string;
          user_role: string;
        };
        Update: {
          created_at?: string;
          deleted_at?: string | null;
          id?: string;
          org_id?: string;
          updated_at?: string;
          user_id?: string;
          user_role?: string;
        };
        Relationships: [
          {
            foreignKeyName: "users_by_organization_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "users_by_organization_user_id_fkey1";
            columns: ["user_id"];
            isOneToOne: false;
            referencedRelation: "user_profiles";
            referencedColumns: ["id"];
          },
        ];
      };
    };
    Views: {
      data_ingestion_as_table: {
        Row: {
          dataset_id: string | null;
          org_id: string | null;
          table_id: string | null;
          table_name: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "materialization_dataset_id_fkey";
            columns: ["dataset_id"];
            isOneToOne: false;
            referencedRelation: "datasets";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "materialization_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      model_as_table: {
        Row: {
          dataset_id: string | null;
          org_id: string | null;
          table_id: string | null;
          table_name: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "model_dataset_id_fkey";
            columns: ["dataset_id"];
            isOneToOne: false;
            referencedRelation: "datasets";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "model_release_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      static_model_as_table: {
        Row: {
          dataset_id: string | null;
          org_id: string | null;
          table_id: string | null;
          table_name: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "static_model_dataset_id_fkey";
            columns: ["dataset_id"];
            isOneToOne: false;
            referencedRelation: "datasets";
            referencedColumns: ["id"];
          },
          {
            foreignKeyName: "static_model_org_id_fkey";
            columns: ["org_id"];
            isOneToOne: false;
            referencedRelation: "organizations";
            referencedColumns: ["id"];
          },
        ];
      };
      table_lookup: {
        Row: {
          dataset_id: string | null;
          logical_fqn: string | null;
          org_id: string | null;
          table_id: string | null;
          table_name: string | null;
          warehouse_fqn: string | null;
        };
        Relationships: [];
      };
    };
    Functions: {
      accept_invitation: {
        Args: { p_invitation_id: string; p_user_id: string };
        Returns: boolean;
      };
      add_credits: {
        Args: {
          p_amount: number;
          p_metadata?: Json;
          p_transaction_type: string;
          p_user_id: string;
        };
        Returns: boolean;
      };
      can_grant_permission: {
        Args: {
          granter_id: string;
          permission_to_grant: string;
          target_resource_id: string;
          target_resource_type: string;
          target_user_id?: string;
        };
        Returns: boolean;
      };
      check_org_admin: {
        Args: { check_org_id: string; check_user_id: string };
        Returns: boolean;
      };
      check_org_membership: {
        Args: { check_org_id: string; check_user_id: string };
        Returns: boolean;
      };
      check_resource_permission: {
        Args: { p_resource_id: string; p_resource_type: string };
        Returns: Json;
      };
      cleanup_orphaned_invitations: { Args: never; Returns: undefined };
      deduct_credits: {
        Args: {
          p_amount: number;
          p_api_endpoint?: string;
          p_metadata?: Json;
          p_transaction_type: string;
          p_user_id: string;
        };
        Returns: boolean;
      };
      expire_old_invitations: { Args: never; Returns: undefined };
      get_og_image_info: {
        Args: { p_notebook_name: string; p_org_name: string };
        Returns: Json;
      };
      get_organization_credits: { Args: { p_org_id: string }; Returns: number };
      get_user_credits: { Args: { p_user_id: string }; Returns: number };
      hasura_token_hook: { Args: { event: Json }; Returns: Json };
      preview_deduct_credits: {
        Args: {
          p_amount: number;
          p_api_endpoint?: string;
          p_metadata?: Json;
          p_transaction_type: string;
          p_user_id: string;
        };
        Returns: boolean;
      };
      uuid_or_null: { Args: { str: string }; Returns: string };
      validate_ownership_limits: {
        Args: {
          p_current_record_id?: string;
          p_new_role: string;
          p_old_role?: string;
          p_user_id: string;
        };
        Returns: boolean;
      };
    };
    Enums: {
      dataset_type:
        | "USER_MODEL"
        | "DATA_CONNECTOR"
        | "DATA_INGESTION"
        | "STATIC_MODEL";
      model_kind:
        | "INCREMENTAL_BY_TIME_RANGE"
        | "INCREMENTAL_BY_UNIQUE_KEY"
        | "INCREMENTAL_BY_PARTITION"
        | "SCD_TYPE_2_BY_TIME"
        | "SCD_TYPE_2_BY_COLUMN"
        | "FULL"
        | "VIEW";
      run_status: "running" | "completed" | "failed" | "canceled" | "queued";
      run_type: "manual" | "scheduled";
      step_status: "running" | "success" | "failed" | "canceled";
    };
    CompositeTypes: {
      model_column_type: {
        name: string | null;
        type: string | null;
        description: string | null;
      };
      model_dependency_type: {
        model_id: string | null;
        alias: string | null;
      };
      model_kind_options: {
        time_column: string | null;
        time_column_format: string | null;
        batch_size: number | null;
        lookback: number | null;
        unique_key_columns: string[] | null;
        when_matched_sql: string | null;
        merge_filter: string | null;
        valid_from_name: string | null;
        valid_to_name: string | null;
        invalidate_hard_deletes: boolean | null;
        updated_at_column: string | null;
        updated_at_as_valid_from: boolean | null;
        scd_columns: string[] | null;
        execution_time_as_valid_from: boolean | null;
      };
    };
  };
};

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">;

type DefaultSchema = DatabaseWithoutInternals[Extract<
  keyof Database,
  "public"
>];

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R;
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R;
      }
      ? R
      : never
    : never;

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I;
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I;
      }
      ? I
      : never
    : never;

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U;
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U;
      }
      ? U
      : never
    : never;

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never;

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals;
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never;

export const Constants = {
  public: {
    Enums: {
      dataset_type: [
        "USER_MODEL",
        "DATA_CONNECTOR",
        "DATA_INGESTION",
        "STATIC_MODEL",
      ],
      model_kind: [
        "INCREMENTAL_BY_TIME_RANGE",
        "INCREMENTAL_BY_UNIQUE_KEY",
        "INCREMENTAL_BY_PARTITION",
        "SCD_TYPE_2_BY_TIME",
        "SCD_TYPE_2_BY_COLUMN",
        "FULL",
        "VIEW",
      ],
      run_status: ["running", "completed", "failed", "canceled", "queued"],
      run_type: ["manual", "scheduled"],
      step_status: ["running", "success", "failed", "canceled"],
    },
  },
} as const;
